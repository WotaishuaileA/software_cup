
-- read the malware data
--	 in setup mode 
--	- read all the files
--  - decide if it should be in dataset
--  - save a list of all files
--  - 			

-- read the whole program into a tensor
function readfileFunc_tensor(filename)

	local contents = {}

	local f = torch.DiskFile(filename)
	f.quiet(f)
	local c = 'a'
	local count = 0
	local func = {}

	for i = 1,opt.kernelLength do
		table.insert(func,1)
		count = count + 1
	end

	local nFuncs = 0
	while c ~= '' do --and count <= opt.programLen do -- potential bug...
		c = f.readString(f,'*l')
		c = c:gsub('[\r\n]+', '')
		local len = #c
		if len > 0 then

			for k = 1,len,2 do
				local num = string.sub(c,k,k+1)
				local n = tonumber(num,16)
				if n == nil then  
					error("无法将 '" .. filename .. "' 的 '" .. k .. "' , '" .. num .. "' 转换为十六进制数")  -- 如果转换失败，则抛出错误  
				end
				table.insert(func,n + 2) -- plus 2 so that our lowest symbol is '2' i.e. no_op is '2'
				count = count + 1
			end
			nFuncs = nFuncs + 1

			for i = 1,opt.kernelLength do
				table.insert(func,1)
				count = count + 1
			end

			if opt.markFunctionEnds then
				table.insert(func,255) -- mark the end of each function
			end
		end
	end
	return torch.ByteTensor(func),nFuncs,count
end

-- get an upper bound on the number of malware files
-- we will discard some files that are too short etc
function upperBoundNumberOfFiles(rootDir)
	local numberOfFilesBound = 0
	local malwareDirs = paths.dir(rootDir)	
	for i = 1,#malwareDirs do
		local dir = malwareDirs[i]
		if dir ~= '.' and dir ~= '..' and paths.dirp(paths.concat(rootDir,dir)) then
			local malwarefiles = paths.dir(paths.concat(rootDir,dir))	
			-- number of files minus '.' and '..'
			numberOfFilesBound = numberOfFilesBound + #malwarefiles - 2
		end
	end
	print('upper bound number of programs ',numberOfFilesBound)
	return numberOfFilesBound
end

-- this function gets called once when processing a new dataset
-- we read all the programs and decide which ones should be included
-- we just use an arbitrary rule that excludes very short programs
-- the list of included programs is returned and saved for later use
function readMalwareData_setup(rootDir)

	-- read all the directories
	-- check each file to see if it meets some criterion
	-- save list of filenames
	-- split into train / test sets

	local datasetInfo = {
		filesList = {},
		family = {},
		familyName = {},
		label = {},
		benignFamily = -1,
	}

	local programCount = 0
	local familyNumber = 1

	local malwareDirs = paths.dir(rootDir)

	for i = 1,#malwareDirs do
		local dir = malwareDirs[i]
		if dir ~= '.' and dir ~= '..' and paths.dirp(paths.concat(rootDir,dir)) then
			local malwarefiles = paths.dir(paths.concat(rootDir,dir))			
			for f = 1,#malwarefiles do
				local file = malwarefiles[f]
				if file ~= '.' and file ~= '..' then
					local contents,nFuncs = readfileFunc_tensor(paths.concat(rootDir,dir,malwarefiles[f]))					
					if nFuncs >= 8 then -- a bit arbitrary... basically we want to ignore very short files

						programCount = programCount + 1
						if programCount % 100 == 0 then
							print('programs read ',programCount,collectgarbage("count"))
							collectgarbage()
						end
						
						-- local includeFile = dir .. '/' .. malwarefiles[f]						
						table.insert(datasetInfo.filesList,malwarefiles[f])
						table.insert(datasetInfo.family,familyNumber)

						if dir == 'Benign' then
							datasetInfo.benignFamily = familyNumber
							table.insert(datasetInfo.label,1)
						else                                
							table.insert(datasetInfo.label,2)
						end

					end
				end
			end
			familyNumber = familyNumber + 1
			table.insert(datasetInfo.familyName,dir)
		end
	end

	datasetInfo.family = torch.Tensor(datasetInfo.family)
	datasetInfo.label = torch.Tensor(datasetInfo.label)

	return datasetInfo
end

-- reads the malware data into a tensor
-- We read all the opcodes into a single block of memory
-- this is because each program can be a different length
-- so storing in a 2D array will waste lots space
-- We also can't use a Lua list as they are limited to 2GB
--
-- allData.program          - tensor (i.e. 1D array of bytes) containing all opcodes
-- allData.programStartPtrs - pointers to start of each program in allData.program
-- allData.programLengths   - the length of each opcode sequence
--
-- For example, to access program 3 do
--
-- local ptr = allData.programStartPrts[3]
-- local len = allData.programLengths[3]
-- local prog = allData.program[{{ptr,ptr + len - 1}}]
--
function readMalwareData(rootDir,metaData)

	print('reading files with version 2')

	local malwareDirs = paths.dir(rootDir)	
	local upperBoundNumFiles = upperBoundNumberOfFiles(rootDir)

	local meanProgramLen = 50000

	local allData = {
		program = torch.ones(upperBoundNumFiles * meanProgramLen):byte(),
		programStartPtrs = {},
		programLengths = {},
	}

	local programLen = {}

	local progPtr = 1
	local programCount = 0

	for i = 1,#metaData.filesList do

		local file = metaData.filesList[i]
		local familyDir = metaData.familyName[metaData.family[i]]
		local fullFile = paths.concat(rootDir,familyDir,file)

		if paths.filep(fullFile) then			

			local contents = readfileFunc_tensor(fullFile)

			programCount = programCount + 1
			if programCount % 100 == 0 then
				print('programs read ',programCount,collectgarbage("count"))
				collectgarbage()
			end

			local programLength = contents:size(1)

			-- if needed - increase the size of the storage
			if (progPtr + programLength - 1) > allData.program:size(1) then
				local currSize = allData.program:size(1)
				allData.program = allData.program:resize(currSize * 1.05)
			end

			table.insert(allData.programStartPtrs,progPtr)
			table.insert(allData.programLengths,programLength)

			-- insert the program into the memory
			allData.program[{{progPtr,progPtr + programLength - 1}}] = contents
			progPtr = progPtr + programLength
		else
			-- we should stop if this happens!
			error('ERROR : Missing file in dataset : ' .. fullFile)
		end
	end

	allData.program = allData.program:resize(progPtr) -- discard redundant rows
	allData.programStartPtrs = torch.Tensor(allData.programStartPtrs)
	allData.programLengths = torch.Tensor(allData.programLengths)
	allData.label = metaData.label

	return allData,programLen
end
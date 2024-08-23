-- Example of how to test using a pre-trained network
-- Expects a directory containing two or more directories
-- One directory contains all the malware
-- The other directory contains all the benign software

-- given a model that has already been trained
-- and a directory containing programs - classify into malware / benign

require 'nn'
require 'optim'

require 'readfileFunc_tensor'
require 'testModel'
function extractFilename(path)  
	 -- 查找最后一个'/'或'\'的位置  
	local pos = string.rfind(path, [[\\/]])  
	if pos == -1 then  
		-- 如果没有找到'/'或'\'，则整个字符串就是文件名（或路径错误）  
		return path  
	else  
		return string.sub(path, pos + 1)  
	end  
end  
  
-- 注意：Lua标准库中没有string.rfind函数，我们需要自己实现它  
function string.rfind(s, pat, startPos, plain)  
	startPos = startPos or string.len(s)  
	local pos, len = string.find(s, pat, startPos, plain)  
	return pos or -1  
end

cmd = torch.CmdLine()
cmd:option('-useCUDA',false,'use CUDA optimisation')
cmd:option('-dataPath','./malwareDataset/','directory with the android programs to classify')
cmd:option('-modelPath','model.th7','path to model to use for testing')
opt = cmd:parse(arg)
local filePath = extractFilename(opt.dataPath)
local file = io.open('./temp/'..filePath..'.result.txt', "w")  
if file == nil then  
    print("无法打开文件")  
    return  
end
print('loading model from disk')
savedModel = torch.load(opt.modelPath)
print('loaded model')
print(savedModel.trainedModel)

-- we need these values to correctly prepare the files when reading from disk
opt.programLen = savedModel.opt.programLen
opt.kernelLength = savedModel.opt.kernelLength
opt.maxSequenceLength = savedModel.opt.maxSequenceLength
print('reading data from disk')
contents = readfileFunc_tensor(opt.dataPath,savedModel.metaData)

if opt.useCUDA then
	savedModel.trainedModel:cuda()
end
savedModel.trainedModel:evaluate()

print('starting test')
testResult,confidence,time = testModel(contents,savedModel.trainedModel,savedModel.metaData.testInds,0)

print('Results')
print('label   ',testResult)
if testResult == 1 then
	print('Benign')
	file:write('Benign\n')
else
	print('Malware')
	file:write('Malware\n')
end
print(confidence)
	file:write(confidence)
file:close()
print('--')
print('time to complete test (s) :',time)
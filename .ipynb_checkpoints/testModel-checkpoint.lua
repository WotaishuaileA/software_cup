function testModel(contents,model,valInds,epochError)

	print('testing corrected verison 2')
	local confmat = torch.zeros(2,2)
	local timerTest = torch.Timer()

	local dtype = 'torch.DoubleTensor'
	local criterion = nn.ClassNLLCriterion():type(dtype)
	model:evaluate()
	local currProgramPtr = 1
	local currProgramLen = contents:size(1)
	if currProgramLen > opt.maxSequenceLength then
		currProgramLen = opt.maxSequenceLength
	end			

	local valBatch = torch.zeros(1,currProgramLen):type(dtype)
	print(currProgramLen)
	valBatch[{{1},{}}] = contents[{{currProgramPtr,currProgramPtr + currProgramLen - 1}}]
	local netOutput = model:forward(valBatch) 
	local netOutputProb = nn.Exp():forward(netOutput:double())
	local v,i = torch.max(netOutputProb,2)
	local pred = i[{1,1}]
	local time = timerTest:time().real	
	collectgarbage()

	return pred,netOutputProb[{1,pred}],time
end
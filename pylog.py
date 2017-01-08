import importlib
import os

def functionCallerParser(line: str) -> str:
    strPartWeCareAbout = line.split(")")[0]
    parenthesisSplit = strPartWeCareAbout.split("(")
    funcName = parenthesisSplit[0].strip()[3:].strip()
    params = list(map( lambda x: x.split(":")[0],parenthesisSplit[1].split(","))) # get the params for the function
    if params[0] == '':
        params = []
    return funcName, params

class PyLog():
    def __init__(self,fileAdder="__",indentingWith='  ',variableNameStart='__',outputVariableName='output_{}'):
        """output needs to be formattable to add the function name"""
        self.fileAdder = fileAdder
        self.indentingWith = indentingWith
        self.variableNameStart = variableNameStart
        self.outputVariableName = outputVariableName

    def _parsePathAndReturnNewFile(self,path: str) -> str:
        head, fileName = os.path.split(path)
        if fileName.split(".")[-1] != 'py': # if its not a python file
            pass # TODO: do something here
        return path[:-3] + self.fileAdder + '.py', fileName[:-3]
    def _getIndent(self,line: str) -> str:
        if line.strip() == '':
            return ''
        firstCharIdx = next(i for i, j in enumerate(line) if j.strip())
        return firstCharIdx * self.indentingWith

    def beforeFunctionCallCode(self,fileToWriteTo,lineIndents: str,params: list,fileName: str, funcName: str) -> str:
        fileToWriteTo.write(lineIndents + 'try:\n')
        lineIndents += self.indentingWith
        variableName = "{}{}_{}".format(self.variableNameStart,fileName, funcName)
        fileToWriteTo.write("{}{}=open(\'{}.{}.txt\','a+')".format(lineIndents,variableName,fileName, funcName) + "\n") # open file open
        paramContentsStr = "''"
        if len(params):
            paramContentsStr = "\'{}\'.format({})".format(('{},' * len(params)),','.join(params)) # write input to file
        fileToWriteTo.write("{}{}.write({})\n".format(lineIndents,variableName,paramContentsStr))
        return variableName

    def afterFunctionCallCode(self,fileToWriteTo,funcName: str,funcCaller:str,lineIndents: str,fileVariableName: str) -> str:
        outputVar = self.outputVariableName.format(funcName)
        fileToWriteTo.write("{}{}={}\n".format(lineIndents, outputVar, funcCaller))  # get output of function, TODO: check if complex type?
        fileToWriteTo.write("{}{}.write(\"{}\\n\".format({},time.time()))\n".format(lineIndents, fileVariableName, "{},{}", outputVar)) # write output to file with timestamp
        fileToWriteTo.write("{}{}.close()\n".format(lineIndents, fileVariableName)) # close file
        fileToWriteTo.write(lineIndents[:-len(self.indentingWith)] + "except:\n") # add except block from try
        fileToWriteTo.write(lineIndents + "pass\n")  # TODO: throw an error, and parse line number, maybe keep offset in a dictionary?

    def import_file(self,path: str,package='',functionToLog='all',functionsNotToAdd=None):
        with open(path,'r') as f:
            fileContents = f.read().split("\n")
        newPath,fileName = self._parsePathAndReturnNewFile(path)
        newFileName = fileName + self.fileAdder
        with open(newPath,'w') as f:
            in_func = False
            funcCaller = funcName = fileVariableName = indent = ''
            f.write('import time\n')
            for i,line in enumerate(fileContents):
                lineIndent = self._getIndent(line)
                if line.strip()[:3] == 'def':
                    if in_func:
                        self.afterFunctionCallCode(f, funcName, funcCaller, indent, fileVariableName)
                    in_func = True
                    funcName, params = functionCallerParser(line)
                    funcCaller = "{}({})".format(funcName,','.join(params))
                    f.write(line +"\n") # our definition of function that gets called by user
                    fileVariableName = self.beforeFunctionCallCode(f,lineIndent + self.indentingWith,params,fileName,funcName)
                    indent = lineIndent + self.indentingWith*2
                    f.write(indent + line + "\n") # internal definition of function, that we will call
                elif in_func and len(lineIndent) < len(indent): # did we exit the function?
                    # TODO: could in parenthesis bugs, where the line doesn't need to be indented, need to check previous line?
                    # TODO: or keep track with some stack that we are in a parenthesis
                    # TODO: to optimize, don't always recalculate len(indent)?
                    self.afterFunctionCallCode(f,funcName,funcCaller,indent,fileVariableName)
                    in_func = False
                    indent = lineIndent
                    f.write(lineIndent + line + "\n")
                elif in_func: # in function, lets write the line
                    f.write(indent + line +"\n") # TODO: check if calling a function we have defined, and call ours
                else: # otherwise just write line
                    f.write(line+"\n") # TODO: check if calling a function we have defined, and call ours
        importlib.invalidate_caches() # invalidate, so we can reload new files
        return importlib.import_module(newFileName) # import it
from genericpath import exists
import os
def createFile(fl, extention ,Exec):
    file = open(fl + '.' + extention, 'a')
    file = open(fl + '.' + extention, 'r+')

    
    if file.mode == 'r+':

        content = file.read()
        #pfile = open(fl + '.py', 'w+')
        #pcon = pfile.write(content)
        if extention == 'ech':
            content = content.replace('-', '	')
            content = content.replace('function UPDATE', 'while True:')
            content = content.replace('function', 'def')
            content = content.replace('embed', 'import')
            
            
            
        
        
        
        
        if Exec:
            exec(content)
        
        
    else:
        print("failed")

def createFolder(fl, path):
    
    os.chdir(path)
    
    
    
    os.makedirs(fl)




createFile('normal_script', 'ech' ,True)




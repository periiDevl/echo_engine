def intro(fl, Exec):
   
    file = open(fl + '.txt', 'a')
    file = open(fl+'.txt', 'r')
    if file.mode == 'r':
        content = file.read()
        pfile = open(fl + '.py', 'w+')
        
        pcon = pfile.write(content)
        
        
        if Exec:
            exec(content)
        
        
    else:
        print("failed")


intro('importer', True)
import importer




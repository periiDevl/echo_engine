def intro(fl, Exec):
   
    file = open(fl + '.ech', 'a')
    file = open(fl+'.ech', 'r')
    if file.mode == 'r':
        content = file.read()
        pfile = open(fl + '.py', 'w+')
        
        
        content = content.replace('-', '	')
        
        print(content)
        pcon = pfile.write(content)
        
        
        if Exec:
            exec(content)
        
        
    else:
        print("failed")


intro('normal_script', True)





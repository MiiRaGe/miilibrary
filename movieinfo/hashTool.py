'''
File imported from HashSourceCodes
License GPL
'''
import struct, os, hashlib

def hashFile(name): 
    try: 
         
        longlongformat = 'q'  # long long 
        bytesize = struct.calcsize(longlongformat) 
            
        f = open(name, "rb") 
            
        filesize = os.path.getsize(name) 
        hashTemp = filesize 
            
        if filesize < 65536 * 2: 
            return "SizeError" 
         
        for x in range(65536 / bytesize): 
            bufferTemp = f.read(bytesize) 
            (l_value,) = struct.unpack(longlongformat, bufferTemp)  
            hashTemp += l_value 
            hashTemp = hashTemp & 0xFFFFFFFFFFFFFFFF  # to remain as 64bit number  
             
        
        f.seek(max(0, filesize - 65536), 0) 
        for x in range(65536 / bytesize): 
                bufferTemp = f.read(bytesize) 
                (l_value,) = struct.unpack(longlongformat, bufferTemp)  
                hashTemp += l_value 
                hashTemp = hashTemp & 0xFFFFFFFFFFFFFFFF 
         
        f.close() 
        returnedhash = "%016x" % hashTemp 
        return returnedhash 
    except(IOError): 
                return "IOError"


#this hash function receives the name of the file and returns the hash code
def get_hash(name):
    readsize = 64 * 1024
    f = open(name, 'rb')
    if f:
        size = os.path.getsize(name)
        data = f.read(readsize)
        f.seek(-readsize, os.SEEK_END)
        data += f.read(readsize)
    return hashlib.md5(data).hexdigest()
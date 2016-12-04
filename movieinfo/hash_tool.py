'''
File imported from HashSourceCodes
License GPL
'''
import os
import struct


def hash_file(name):
    try: 
        longlongformat = 'q'  # long long
        bytesize = struct.calcsize(longlongformat) 
            
        file_descripter = open(name, 'rb')
            
        filesize = os.path.getsize(name)
        hash_temp = filesize
            
        if filesize < 65536 * 2: 
            return 'SizeError'
         
        for x in range(65536 // bytesize):
            buffer_temp = file_descripter.read(bytesize)
            (l_value,) = struct.unpack(longlongformat, buffer_temp)
            hash_temp += l_value
            hash_temp &= 0xFFFFFFFFFFFFFFFF  # to remain as 64bit number

        file_descripter.seek(max(0, filesize - 65536), 0)
        for x in range(65536 // bytesize):
                buffer_temp = file_descripter.read(bytesize)
                (l_value,) = struct.unpack(longlongformat, buffer_temp)
                hash_temp += l_value
                hash_temp &= 0xFFFFFFFFFFFFFFFF
         
        file_descripter.close()
        returned_hash = '%016x' % hash_temp
        return returned_hash
    except IOError as e:
        return 'IOError'

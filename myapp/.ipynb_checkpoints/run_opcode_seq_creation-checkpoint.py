#!/usr/bin/env python
import sys
import os
import shutil
import datetime
import logging

# sys.path.insert(1, os.path.join(sys.path[0], '../..'))

def run_opcode_seq_creation(apk_name):

    num_local = 0
    before=datetime.datetime.now()
    print('Starting at: {0}'.format(before))

    # Looping through all apks
    opseq_file_directory = "opseq"
    decoded_location = os.path.join("decoded_apks", apk_name)
    if not os.path.exists(os.path.join(opseq_file_directory,f"{apk_name}.opseq")):
        result =create_opcode_seq(decoded_location,opseq_file_directory,apk_name)


    after=datetime.datetime.now()

def create_opcode_seq(decoded_dir,opseq_file_directory,apk_hash):
    # Returns true if creating opcode sequence file was successful,
    # searches all files in smali folder,
    # writes the coresponding opcode sequence to a .opseq file
    # and depending on the include_lib value,
    # it includes or excludes the support library files

    dalvik_opcodes = {}
    # Reading Davlik opcodes into a dictionary
    with open("DalvikOpcodes.txt") as fop:
        for linee in fop:
            (key, val) = linee.split()
            dalvik_opcodes[key] = val
    try:
        smali_dir = os.path.join(decoded_dir, "smali")
        opseq_fname=os.path.join(opseq_file_directory,apk_hash+".opseq")

        with open(opseq_fname, "a") as opseq_file:
            for root, dirs, fnames in os.walk(smali_dir):
                for fname in fnames:
                    full_path = os.path.join(root, fname)
                    opseq_file.write(get_opcode_seq(full_path, dalvik_opcodes))
                    print("path:"+full_path)
        opseq_file.close()

        return True
    except Exception as e:
        logging.error('Exception occured during opseq creation {0}'.format(str(e)))
        return False

def get_opcode_seq(smali_fname, dalvik_opcodes):
    # Returns opcode sequence created from smali file 'smali_fname'.

    opcode_seq=''

    with open(smali_fname, mode="r") as bigfile:
        reader = bigfile.read()
        for i, part in enumerate(reader.split(".method")):
            add_newline = False
            if i!=0:
                method_part=part.split(".end method")[0]
                method_body = method_part.strip().split('\n')
                for line in method_body:
                    if not line.strip().startswith('.') and not line.strip().startswith('#') and line.strip():
                        method_line = line.strip().split()
                        if method_line[0] in dalvik_opcodes:
                            add_newline = True
                            opcode_seq += dalvik_opcodes[method_line[0]]
                if  add_newline:
                    opcode_seq += '\n'
    return opcode_seq

def decode_application (apk_file_location,tmp_file_directory,hash,include_libs):
    # Decodes the apk at apk_file_location and
    # stores the decoded folders in tmp_file_directory

    out_file_location = os.path.join(tmp_file_directory, hash+ ".smali")
    try:
        apktool_decode_apk( apk_file_location, out_file_location,include_libs )
    except ApkToolException:
        logging.error("ApktoolException on decoding apk  {0} ".format(apk_file_location))
        pass
    return out_file_location

if __name__ == '__main__':
    main()

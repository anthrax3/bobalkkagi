from unicorn import *
from unicorn.x86_const import *
from capstone import *
from loader import DLL_Loader, Insert_IAT
from logger import *
from datetime import datetime
from api_hook import *
from config import DLL_SETTING
from peb import SetLdr, SetListEntry, SetProcessHeap, SetPEB
from teb import *

import logging
import config
import struct
import pefile
import os

GS = 0xff10000000000000
ADDRESS = 0x140000000
DLL_BASE = 0x800000
COUNT=0
Ldr = 0x000001B54C810000
PROC_HEAP_ADDRESS=0x000001E9E3850000
STACK_BASE=0x201000
STACK_LIMIT= 0x100000
MB = 2**20 #Mega Byte

#DLL_FUNCTIONS={} # {function name: address}
#LOADED_DLL = {} # {dll: address}

BobLog = logging.getLogger("Bobalkkagi")



def hook_fetch(uc, access, address, size, value, user_data):
    
    print(hex(access),hex(address),hex(size),hex(value))
    rip=uc.reg_read(UC_X86_REG_RIP)
    print(hex(rip))


def hook_block(uc, address, size, user_data):
    
    rsp=uc.reg_read(UC_X86_REG_RSP)
    rip=uc.reg_read(UC_X86_REG_RIP)
    
    #BobLog.debug("DEBUGING")
    
    tmp = {hex(address):size}
    
    if config.get_len() >=config.get_size():
        config.p_queue()
    config.i_queue(tmp)
   
    try :
        if rip in DLL_SETTING.INV_DLL_FUNCTIONS:
            print(DLL_SETTING.INV_DLL_FUNCTIONS[rip])
            globals()['hook_'+DLL_SETTING.INV_DLL_FUNCTIONS[rip].split('.dll_')[1]](rip,rsp,uc,BobLog)
    except KeyError as e:
        BobLog.info("Not Found : "+str(e))

def hook_code(uc, address, size, user_data):
    
    rsp=uc.reg_read(UC_X86_REG_RSP)
    rip=uc.reg_read(UC_X86_REG_RIP)
    
    global COUNT
    global ADDRESS
    
    '''
    tmp = {hex(address):size}
    
    if config.get_len() >=config.get_size():
        config.p_queue()
    config.i_queue(tmp)

    try :
        if rip in InvDllFunctions:
            print(InvDllFunctions[rip])
            globals()['hook_'+InvDllFunctions[rip].split('.dll_')[1]](rip,rsp,uc,BobLog)
    except KeyError as e:
        BobLog.info("Not Found : "+str(e))
    '''

    
    '''
    for section in pe.sections:
        if b'.text' in section.Name:
            handle이 text영역일때로 변경해야함
    '''

    from logger import regis
    import time

    reg = {}

    for key in regis:
        reg[key] = hex(uc.reg_read(regis[key]))

    assem = disas(bytes(uc.mem_read(address, size)), address)

    '''
    print(reg) # 레지스터 변화 확인
    time.sleep(1)
    '''

    for asm in assem:
        config.get_num1()
        if ("jmp" == asm.mnemonic):
            if (config.ret_num2() == -2):
                api_data = reg["RAX"]
                # 처음 call한 부분에서 asm op_str 변경 (원래 api 값이 들어있는 reg값 참조해서?)
                #print(asm)
                #time.sleep(1)
                continue
            config.get_num2()
            continue
        elif ("or" == asm.mnemonic):
            num1_tmp = config.sub_num1()
            num2_tmp = config.ret_num2()
            if(num2_tmp == num1_tmp):
                config.res_num2()
                continue
        config.globar_var.control_num2 = -1

def setup_teb(uc):
    global HEAP_BASE
    teb_addr = 0xff10000000000000
    peb_addr = 0xff20000000000000
    teb = InitTeb()
    teb_payload = bytes(teb)
    uc.mem_map(teb_addr, 2 * 1024 * 1024,UC_PROT_ALL)
    uc.mem_map(peb_addr, 2 * 1024 * 1024,UC_PROT_ALL)
    uc.mem_map(Ldr, 1 * MB, UC_PROT_ALL)
    uc.mem_map(PROC_HEAP_ADDRESS, 10 * MB, UC_PROT_ALL)
    uc.mem_write(teb_addr, teb_payload)
    uc.mem_write(peb_addr+ 0x30, struct.pack('<Q', PROC_HEAP_ADDRESS))
    uc.mem_write(PROC_HEAP_ADDRESS+0x1db0,struct.pack('<Q',0x5A0058))
    uc.mem_write(PROC_HEAP_ADDRESS+0x1db8,struct.pack('<Q',PROC_HEAP_ADDRESS+0x2398))
    uc.reg_write(UC_X86_REG_GS_BASE, teb_addr)
    uc.reg_write(UC_X86_REG_CS, 0x400000)

def emulate(program: str,  verbose):
    start = datetime.now()
    print(f"[{start}]Emulating Binary!")

    DLL_ADDRESS = 0x800000

    pe = pefile.PE(program)
    uc = Uc(UC_ARCH_X86, UC_MODE_64)

    setup_logger(uc, BobLog, verbose)

    EP = pe.OPTIONAL_HEADER.AddressOfEntryPoint #Entry Point

    uc.mem_map(ADDRESS, 20*MB, UC_PROT_ALL)
    uc.mem_map(DLL_BASE, 50*MB, UC_PROT_ALL)
    uc.mem_map(STACK_LIMIT, STACK_BASE - STACK_LIMIT)
    uc.mem_write(ADDRESS, pe.header)
    
    for section in pe.sections:
        code = section.get_data()
        uc.mem_write(ADDRESS + section.VirtualAddress, code)
        if b'.boot' in section.Name:
            bootSize = section.VirtualAddress + section.Misc_VirtualSize

    dllList = [
        "kernel32.dll", "kernelbase.dll", "ntdll.dll", 
        "user32.dll", "ucrtbase.dll",
        "vcruntime140d.dll", "win32u.dll",
        "gdi32.dll", "msvcp_win.dll",
        "advapi32.dll", "shell32.dll", "shlwapi.dll"
        ]
    
    #Load dll
    #DLL_ADDRESS = DLL_Loader(uc, "ntdll.dll", DLL_ADDRESS,"C:\\Users\\kor15\\Desktop\\practice\\bob\\Bobalkkagi_test")
    #DLL_ADDRESS = DLL_Loader(uc, "kernel32.dll", DLL_ADDRESS,"C:\\Users\\kor15\\Desktop\\practice\\bob\\Bobalkkagi_test")
    #DLL_ADDRESS = DLL_Loader(uc, "KernelBase.dll", DLL_ADDRESS,"C:\\Users\\kor15\\Desktop\\practice\\bob\\Bobalkkagi_test")
    for dll in dllList:
        DLL_ADDRESS = DLL_Loader(uc, dll, DLL_ADDRESS)

    setup_teb(uc)
    '''
    SetLdr(uc) # Ldr set     load된 dll마다 추가해줘야 함
    for i in range(0,4):  # ListEntry set 
        SetListEntry(uc,dllList[i],i)
    '''
    uc.mem_write(PROC_HEAP_ADDRESS+0x2398,os.path.abspath(program).encode("utf-8"))
    SetPEB(uc)
    SetProcessHeap(uc)
    Insert_IAT(uc, pe, ADDRESS, DLL_ADDRESS)

    config.InvDllDict()
    
    uc.reg_write(UC_X86_REG_RSP, STACK_BASE - 0x1000) #0x200000
    uc.reg_write(UC_X86_REG_RBP, 0x0) #0x200600a
    
    print("hook start!")
    #uc.hook_add(UC_HOOK_CODE, hook_code)
    uc.hook_add(UC_HOOK_BLOCK, hook_block)
   
    uc.reg_write(UC_X86_REG_RAX, ADDRESS+EP)
    uc.reg_write(UC_X86_REG_RDX, ADDRESS+EP)
    uc.reg_write(UC_X86_REG_R9, ADDRESS+EP)
    
    try:
        uc.emu_start(ADDRESS + EP, ADDRESS + EP + bootSize)
    except UcError as e:
        print(f"[ERROR]: {e}")
        BobLog.debug("DEBUGING")
                  

    end = datetime.now()
    print(f"[{end}] Emulation done...")
    print(f"Runtime: [{end-start}]")
    

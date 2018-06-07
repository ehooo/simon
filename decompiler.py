import base64
import json

import r2pipe

# Load file
r2 = r2pipe.open("malcon2018_flash.hex")
r2.cmd('aaa')  # Analysis
file_info = json.loads(r2.cmd('ij'))  # Read file info
print_info = "File name:{} Size:{}\n" \
             "Format:{} Arch:{}\n" \
             "OS:{} Machine:{}"
print print_info.format(
    file_info['core']['file'],
    file_info['core']['humansz'],
    file_info['core']['format'],
    file_info['bin']['arch'],
    file_info['bin']['os'],
    file_info['bin']['machine'],
)
opcode_size = file_info['bin']['pcalign']  # Useful to read instructions

print "\nStrings:"
strings = json.loads(r2.cmd('izzj'))['strings']
str_info = {}
for line in strings:
    str_raw = base64.standard_b64decode(line['string'])
    if str_raw in ['NEW HI-SCORE!!!', 'Hi-Score: ', '\\nCurrent score: ']:
        paddr = hex(line['paddr'])
        print str_raw, paddr, hex(line['vaddr'])
        str_info[paddr] = str_raw

print "\nSymbols:"  # This is the interruptions
symbols = json.loads(r2.cmd('isj'))
for info in symbols:
    print "{}:\t".format(info['name']), hex(info['paddr'])

print "\nFunctions:"
functions = json.loads(r2.cmd('aflj'))
funct_data = []
for info in functions:
    funct_data.append({
        'name': info['name'],
        'offset': hex(info['offset']),
        'size': hex(info['size'])
    })
    print "{}:\t".format(info['name']), hex(info['offset'])

entry_point = hex(json.loads(r2.cmd('iej'))[0]['paddr'])
print "\nEntryPoint:", entry_point

r2.cmd('s{}'.format(entry_point))  # Go to entry point
decompile = json.loads(r2.cmd('pdfj'))  # Decompile function
if hex(decompile['addr']) != entry_point:
    print "Never happen"
if decompile['size'] != len(decompile['ops']) * opcode_size:
    print "Never happen"

calls = []
for asm in decompile['ops']:
    disasm = asm['disasm']
    if disasm.find('call') != -1:
        calls.append(asm)
    print disasm

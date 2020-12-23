#!/usr/bin/python2.7

from __future__ import print_function
from pprint import pprint
import base64
import binascii
import os


WARNING = '\033[93m'
FAIL = '\033[91m'
ENDC = '\033[0m'
dbg = False

def twos_comp(n, bits=6):
    mask = (1 << bits) - 1
    neg = n ^ mask
    return (neg + 1) & mask


# Helpers
def toOct(n):
	return "0{0:o}".format(n)

def logical_rshift(signed_integer, places, num_bits=32):
    unsigned_integer = signed_integer % (1 << num_bits)
    return unsigned_integer >> places

def logical_lshift(signed_integer, places, num_bits=32):
    unsigned_integer = signed_integer % (1 << num_bits)
    return unsigned_integer << places

def get_key(mydict,val):
    for key, value in mydict.items():
         if val == value:
             return key 
    return "key doesn't exist"

def to_int(n, bits=6):
    '''Turn a two's complement number into a Python int'''
    if (n & (1 << (bits - 1))) != 0:
        n = n - (1 << bits)
    return n

# main routines
def readRom(file):
	"""
	Read rom program and return decoded instructions
	"""
	with open(file,'r') as f:
		data = f.read()
		raw_data = base64.b64decode(data).encode('hex')
		instructions = [raw_data[i:i+6] for i in range(0,len(raw_data),6)]
		instructions = [[i,instructions[i]] for i in range(0,len(instructions),1)]
		return instructions

def findLabels(instructions):
	""" 
	generate table of labels with positions:
	# flags:
	#   0 : False
	#   1 : True
	#   2 : neither
	"""
	pc = 0
	jmps = []
	for pc in range(0,len(instructions)):
		i = instructions[pc][1]
		i = format(int(i[0:2],16),'08b')+format(int(i[2:4],16),'08b')+format(int(i[4:6],16),'08b')
		opc = int(i[0:6],2)
		a = int(i[6:12],2)
		b = int(i[12:18],2)
		c = int(i[18:24],2)

		if (0 < opc ) and (opc <= 19):
			op = opc - 1
			condition = 0
		if (21 < opc ) and (opc <= 40):
			op = opc - 22
			condition = 1
		if (42 < opc ) and (opc <= 61):
			op = opc - 43
			condition = 2
		if op == 15:
		
			a = a
			b = b
			c = c
			lab = 64*a + b
			assert(lab < 4096 and lab >= 0)			
			
			if condition == 1:
				flag = 1
				jmps.append([lab,regs[b],c,pc,flag])
			elif condition == 2:
				flag = 0
				jmps.append([lab,regs[b],c,pc,flag])
			elif condition == 0:
				flag = 2
				jmps.append([lab,regs[b],c,pc,flag])
		pc = pc + 1

	return jmps


def evaluate(instructions,jmps,regs,chardict,devices,ccdict):
	"""
	evaluate list of instructions
	"""
	n = 24
	pc = 0
	
	print("*********** started emulation ***************")
	tty = os.open("/dev/pts/6", os.O_RDWR)
	tty2 = os.open("/dev/pts/1", os.O_RDWR)


	global test
	flag = 1
	clk = 0
	buf = []
	input_buffer = [4,'Y','E','S','\n']
	input_buffer = input_buffer[::-1]
	#while(True):
	while(pc<=525):
		if(pc == 0):
			print("entry:")
		#if(pc == 525):
		#	pc = 0
		#if(clk == 4096):
		#	print("max clk reached")
		#	exit(0)

		assert regs[0] == 0,print("PC={} regs[0]={}".format(pc,regs[0]))

		i = instructions[pc][1]
		i = format(int(i[0:2],16),'08b')+format(int(i[2:4],16),'08b')+format(int(i[4:6],16),'08b')
		opc = int(i[0:6],2)
		a = int(i[6:12],2)
		b = int(i[12:18],2)
		c = int(i[18:24],2)
		Taken = False

		if (0 < opc ) and (opc <= 19):
			op = opc - 1
			condition = 0
		if (21 < opc ) and (opc <= 40):
			op = opc - 22
			condition = 1
		if (42 < opc ) and (opc <= 61):
			op = opc - 43
			condition = 2
		
		assert (opc>0 and opc<=63),print("opc={},i={},a={},b={},c={}".format(opc,i,a,b,c))
		assert (op>=0 and op<20),print("op=",op)

		print(FAIL+" pc = {}".format(pc)+ENDC)

		if op == 0:
			rb = regs[b]
			rc = regs[c]
			
			if condition == 1 and flag == 1:
				condition_flag = '+'
			elif condition == 2 and flag == 2:
				condition_flag = '-'
			else:
				condition_flag = ''
			
			if(condition in [flag,0]):
				taken = True
				regs[a] = (regs[b] + regs[c]) % 64
			
			print("add r{} r{}={} r{}={}    ****** Taken? {}".format(a,b,rb,c,rc,taken))
			print("result: r{} = {}".format(a,regs[a]))

		if op == 1:
			rb = regs[b]
			c = c
			print("op={} rb={} c={} rb+c={}".format(op,regs[b],c,regs[b]+c))
			
			if condition == 1 and flag == 1:
				condition_flag = '+'
			elif condition == 2 and flag == 2:
				condition_flag = '-'
			else:
				condition_flag = ''

			if(condition in [flag,0]):
				taken = True
				regs[a] = (rb + c) % 64
			print("{}add r{} r{}={} {}    ****** Taken? {}".format(condition_flag,a,b,rb,c,taken))
			##print(a,b,regs[b],c)
			print("result: r{} = {}".format(a,regs[a]))

		if op == 2:
			rb = regs[b]
			rc = twos_comp(regs[c])
			
			if condition == 1 and flag == 1:
				condition_flag = '+'
			elif condition == 2 and flag == 2:
				condition_flag = '-'
				skip = True
			else:
				condition_flag = ''
			
			if(condition in [flag,0]):
				taken = True
				regs[a] = (rb + rc)
			print("{}sub r{} r{}={} r{}={}    ****** Taken? {}".format(condition_flag,a,b,regs[b],c,regs[c],taken))
			print("result: r{} = {}".format(a,regs[a]))

		if op == 4:
			rb = regs[b]
			rc = regs[c]
			
			if condition == 1 and flag == 1:
				condition_flag = '+'
			elif condition == 2 and flag == 2:
				condition_flag = '-'
				skip = True
			else:
				condition_flag = ''

			if(condition in [flag,0]):
				taken = True
				regs[a] = (rb | rc) % 64
			print("{}or r{} r{}={} r{}={}    ****** Taken? {}".format(condition_flag,a,b,regs[b],c,regs[c],taken))
			print("result: r{} = {}".format(a,regs[a]))

		if op == 5:
			rb = regs[b]
			c = c
			
			if condition == 1 and flag == 1:
				condition_flag = '+'
			elif condition == 2 and flag == 2:
				condition_flag = '-'
				skip = True
			else:
				condition_flag = ''

			if(condition in [flag,0]):
				regs[a] = (rb | c)  % 64
			print("{}or r{} r{}={} {}    ****** Taken? {}".format(condition_flag,a,b,regs[b],c,taken))
			print("result: r{} = {}".format(a,regs[a]))


		
		if op == 6:
			rb = regs[b]
			rc = twos_comp(regs[c])
			
			if condition == 1 and flag == 1:
				condition_flag = '+'
			elif condition == 2 and flag == 2:
				condition_flag = '-'
			else:
				condition_flag = ''
			
			if(condition in [flag,0]):
				taken = True
				regs[a] = (rb ^ rc) 
			print("{}xor r{} r{}={} r{}={}    ****** Taken? {}".format(condition_flag,a,b,rb,c,rc,taken))
			print("result: r{} = {}".format(a,regs[a]))

		if op == 7:
			rb = regs[b]
			c = c
			

			if condition == 1 and flag == 1:
				condition_flag = '+'
			elif condition == 2 and flag == 2:
				condition_flag = '-'
			else:
				print(condition,flag)
				condition_flag = ''
			
			if(condition in [flag,0]):
				taken = True
				regs[a] = (rb ^ c) % 64
				#print("here")

			print("{}xor r{} r{}={} {}    ****** Taken? {}".format(condition_flag,a,b,regs[b],c,taken))
			print("result: r{} = {}".format(a,regs[a]))

		# 010
		if op == 8:
			rb = regs[b]
			rc = twos_comp(regs[c])
			if condition == 1 and flag == 1:
				condition_flag = '+'
			elif condition == 2 and flag == 2:
				condition_flag = '-'
			else:
				condition_flag = ''

			if(condition in [flag,0]):
				taken = True
				regs[a] = (rb & rc) % 64
			print("{}and r{} r{}={} r{}={}    ****** Taken? {}".format(condition_flag,a,b,regs[b],c,regs[c],taken))
			print("result: r{} = {}".format(a,regs[a]))


		# 011
		if op == 9:
			rb = regs[b]
			c = c
			if condition == 1 and flag == 1:
				condition_flag = '+'
			elif condition == 2 and flag == 2:
				condition_flag = '-'
			else:
				condition_flag = ''
			
			if(condition in [flag,0]):
				taken = True
				regs[a] = (rb & c) % 64
			print("{}and r{} r{}={} {}    ****** Taken? {}".format(condition_flag,a,b,regs[b],c,taken))
			print("result: r{} = {}".format(a,regs[a]))

		# 013
		if op == 11:
			b = regs[b]
			c = regs[c]
			
			if condition == 1 and flag == 1:
				condition_flag = '+'
			elif condition == 2 and flag == 2:
				condition_flag = '-'
			else:
				condition_flag = ''
			
			if(condition in [flag,0]):
				regs[a] = (rb << rc) % 64
			
			print("{}shl r{} r{} r{}    ****** Taken? {}".format(condition_flag,a,b,regs[b],c,taken))
			print("result: r{} = {}".format(a,regs[a]))

		# 014
		# shift reg reg
		if op == 12:
			rb = regs[b]
			rc = regs[c]
			
			if condition == 1 and flag == 1:
				condition_flag = '+'
			elif condition == 2 and flag == 2:
				condition_flag = '-'
			else:
				condition_flag = ''
			
			if(condition in [flag,0]):
				taken = True
				regs[a] = (rb >> rc) % 64
				print("{}shr r{} r{}={} r{}={}    ****** Taken? {}".format(condition_flag,a,b,regs[b],c,regs[c],taken))
				print("result: r{} = {}".format(a,regs[a]))


		#012
		# shift reg imm
		if op == 10:
			
			oc = toOct(c)
			ib = int(oc[-1],10)

			assert (ib >= 0 and ib < 8),print("wtf")
			
			if(condition in [flag,0]):
				taken = True
				if oc[-2] == '0':
					regs[a] = (regs[b] << ib)  % 64
					fcn = 'shl'
				if oc[-2] == '1':
					regs[a] = (regs[b] >> ib)  % 64
					fcn = 'shr'
				if condition == 1 and flag == 1:
					condition_flag = '+'
				elif condition == 2 and flag == 2:
					condition_flag = '-'
				else:
					condition_flag = ''

			print("{}{} r{} r{}={} {}    ****** Taken? {}".format(condition_flag,fcn,a,b,regs[b],c,taken))
			print("result: r{} = {}".format(a,regs[a]))
		
		# 015
		if op == 13:
			
			rb = b
			c = c
			
			if condition == 1 and flag == 1:
				condition_flag = '+'
			elif condition == 2 and flag == 2:
				condition_flag = '-'
			else:
				condition_flag = ''

			if(condition in [flag,0]):
				taken = True
				regs[a] = regs[(rb+c) & 0o77] 
			print("{}ld r{},[r{}={}+{}]    ****** Taken? {}".format(condition_flag,a,b,regs[b],c,taken))
			print("result: r{} = {}".format(a,regs[a]))


		# 016
		if op == 14:
			
			rb = b
			c = c
			if condition == 1 and flag == 1:
				condition_flag = '+'
			elif condition == 2 and flag == 2:
				condition_flag = '-'
			else:
				condition_flag = ''

			if(condition in [flag,0]):
				taken = True
				regs[(rb+c) & 0o77] = regs[a]
			print("{}st [r{}={} +{}], r{}={}    ****** Taken? {}".format(condition_flag,a,b,rb,c,regs[c],taken))
			print("result: r{} = {}".format(a,regs[a]))


		# 017
		if op == 15:
			if(condition in [flag,0]):
				taken = True
				a = a
				b = b
				c = c
				lab = 64*a + b
				assert(lab < 4096 and lab >= 0)
				print("lbl {}:{}    ****** Taken? {}".format(lab,c,taken))
				pc = pc + 1
				clk = clk + 1
				continue
		


		# 003
		# cmp
		# flag = 2 -> False 
		# flag = 1 -> True
		# flag = 0 -> unconditional execution
		
		if op == 3:
			a = toOct(a)
			cc = int(a[-1],10)
			rrb = ''
			rrc = ''
			if condition == 1 and flag == 1:
				condition_flag = '+'
			elif condition == 2 and flag == 2:
				condition_flag = '-'
			else:
				condition_flag = ''
			if(condition in [flag,0]):
				taken = True
				if a[-2] == '0':
					b = regs[b]
					c = regs[c]
					rrb = 'r'
					rrc = 'r'
				if a[-2] == '2':
					b = regs[b]
					c = c
					rrb = 'r'
				if a[-2] == '3':
					b = b
					c = regs[c]
					rrc = 'r'
				ext = ccdict[cc]
				if ext == 'tr':
					flag = 1
				if ext == 'fa':
					flag = 2
				elif ext == 'eq':
					if(b == c):
						flag = 1
					else:
						flag = 2
				elif ext == 'ne':
					if(b != c):
						flag = 1
					else:
						flag = 2
				elif ext == 'ul':
					if(b < c):
						flag = 1
					else:
						flag = 2
				elif ext == 'ug':
					if(b > c):
						flag = 1
					else:
						flag = 2		
				elif ext == 'sl':
					if(to_int(b) < to_int(c)):
						flag = 1
					else:
						flag = 2				
				elif ext == 'sg':
					if(to_int(b) > to_int(c)):
						flag = 1
					else:
						flag = 2

				assert (flag == 1 or flag == 2 or flag == 0)
				print("{}: {}cmp{} {}{}={} {}{}={}    ****** Taken? {}".format(flag,condition_flag,ext,rrb,b,regs[b],rrc,c,regs[c],taken),end='')
				#if(condition in [flag,0]):
				#	raw_input()

		# 020 jup lab,rc
		# REMEMBER: jmps.append([lab,regs[b],c,pc,flag])
		if op == 16:
			b = b
			c = regs[c]
			lab = 64*a + b
			found = False
			assert(lab < 4096 and lab >= 0)
			if condition == 1 and flag == 1:
				condition_flag = '+'
			elif condition == 2 and flag == 2:
				condition_flag = '-'
			else:
				condition_flag = ''
			if(condition in [flag,0]):
				taken = True
				for cnt in range(len(jmps)-1,-1,-1):
					#pprint(jmps)
					if((flag == jmps[cnt][4]) and pc > jmps[cnt][3] and jmps[cnt][0] == lab and c == jmps[cnt][2]):
						print("jmpup {}    ****** Taken? {}".format(jmps[cnt][3],taken))
						pc = jmps[cnt][3]
						found = True
						break
				if(not found):
					print("jmp {}:{} not taken".format(lab,regs[b],c))					
					pc = pc + 1
				#print("")
				#raw_input()
				clk = clk + 1
				continue


		# 021 jdn lab,rc
		# REMEMBER: jmps.append([lab,regs[b],c,pc,flag])
		if op == 17:
			found = False
			a = a
			b = b
			c = regs[c]
			lab = 64*a + b
			assert(lab < 4096 and lab >= 0)
			if condition == 1 and flag == 1:
				condition_flag = '+'
			elif condition == 2 and flag == 2:
				condition_flag = '-'
			if(condition in [flag,0]):
				taken = True
				for cnt in range(0,len(jmps),1):
					if((flag == jmps[cnt][4]) and pc < jmps[cnt][3] and lab == jmps[cnt][0] and c == jmps[cnt][2]):
						print("jmp {}    ****** Taken? {}".format(jmps[cnt][3],taken))
						pc = jmps[cnt][3]
						found = True
						break
				if(not found):
					print("jmpdn {}:{} not taken".format(lab,regs[b],c))					
					pc = pc + 1
				clk = clk + 1
				continue

		# 022
		if op == 18:
			"""
			ix= 0: SERIAL_INCOMING  Reads the number of buffered incoming words, clamped to max 63.
			ix= 1: SERIAL_READ  Reads the next buffered word, -1 if there are none.
			ix= 2: SERIAL_WRITE  Writes send a word to the remote machine.
			* Writing a nonzero value to either device resets the counter to 0.
			
			   a   b   c
			io rd, ix, rs ==> sends rs to device ix and receive rd
			"""

			a = a
			b = b
			c = c

			if condition == 1 and flag == 1:
				condition_flag = '+'
			elif condition == 2 and flag == 2:
				condition_flag = '-'
			else:
				condition_flag = ''
						

			if(condition in [flag,0]):
				taken = True
				if b == 0:
					inp = input_buffer.pop()
					devices[b].append(inp)
					regs[a] = inp
					os.write(tty2, "\r\nb={},regs[{}]={},chardict={},regs[{}]={}    ****** Taken? {}".format(b,c,regs[c],chardict[regs[c]],a,regs[a],taken))
					#raw_input()
					#exit()

				elif b == 1:
					# YES\n 34-14-28-62
					inp = input_buffer.pop()
					#print(type(inp))
					key = get_key(chardict,inp)
					print("Entered:",chardict[key])
					devices[b].append(inp)
					regs[a] = key
					os.write(tty2, "\r\nb={},regs[{}]={},chardict={},regs[{}]={}    ****** Taken? {}".format(b,c,regs[c],chardict[key],a,regs[a],taken))
					
				elif b == 2:
					regs[a]	= regs[c]
					devices[b].append(regs[c])
					os.write(tty, chardict[regs[c]])
					#raw_input()
				else:
					raw_input()
					if(len(devices[b]) != 0):
						peek = devices[b][-1]
					else:
						peek = 1
					regs[a]	= 20
					devices[b].append(regs[c])
					#print("else")
					test.append([b,regs[b],chardict[regs[c]]])
					os.write(tty2, "b={},regs[{}]={},chardict={},regs[{}]={}\n".format(b,b,regs[b],chardict[regs[c]],a,regs[a]))

				print("{}io r{}, device:{}, r{}={}={}    ****** Taken? {}".format(condition_flag,a,b,c,regs[c],chardict[regs[c]],taken))
				regs[0] = 0
				pc = pc + 1
				clk = clk + 1
				assert (b>=0 and b<=63),print(b)
			continue


		if pc == 264:
			print("stop")
			exit()

		if op == 20:
			print("halt")
			exit()

		pc = pc + 1
		clk = clk + 1

	print("*********** fin **********")


if __name__ == '__main__':

	regs = {
		0:0,1:0,2:0,3:0,4:0,5:0,6:0,7:0,8:0,9:0,
		10:0,11:0,12:0,13:0,14:0,15:0,16:0,17:0,18:0,19:0,
		20:0,21:0,22:0,23:0,24:0,25:0,26:0,27:0,28:0,29:0,
		30:0,31:0,32:0,33:0,34:0,35:0,36:0,37:0,38:0,39:0,
		40:0,41:0,42:0,43:0,44:0,45:0,46:0,47:0,48:0,49:0,
		50:0,51:0,52:0,53:0,54:0,55:0,56:0,57:0,58:0,59:0,
		60:0,61:0,62:0,63:0
	}

	charset = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', ' ', '+', '-', '*', '/', '<', '=', '>', '(', ')', '[', ']', '{', '}', '#', '$', '_', '?', '|', '^', '&', '!', '~', ',', '.', ':', '\n','\xff']
	chardict = {}
	for i in range(0,len(charset),1):
	  chardict.update({i:charset[i]})

	devices = {
		0: [], # SERIAL_INCOMING
		1: [], # SERIAL_READ
		2: [], # SERIAL_WRITE
		4: [], # ??
	}

	ccdict = {
		0: 'tr',
		1: 'fa',
		2: 'eq',
		3: 'ne',
		4: 'sl',
		5: 'sg',
		6: 'ul',
		7: 'ug'
	}

	test = []

	instructions = readRom("mandelflag.rom")
	jmps = findLabels(instructions)
	#try:
	evaluate(instructions,jmps,regs,chardict,devices,ccdict)
	#except:
	#	pprint(devices)

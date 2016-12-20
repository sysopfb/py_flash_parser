import struct
import sys
import bitstring
import binascii
import zlib

Tags = {0: "End",
	1: "ShowFrame",
	2: "DefineShape",
	4: "PlaceObject",
	5: "RemoveObject",
	6: "DefineBits",
	8: "JPEGTables",
	9: "SetBackgroundColor",
	10: "DefineFont",
	12: "DoAction",
	13: "DefineFontInfo",
	20: "DefineBitsLossless",
	21: "DefineBitsJPEG2",
	22: "DefineShare2",
	24: "Protect",
	26: "PlaceObject2",
	28: "RemoveObject2",
	32: "DefineShape3",
	35: "DefineBitsJPEG3",
	36: "DefineBitsLossless2",
	41: "ProductInfo",
	43: "FrameLabel",
	46: "DefineMorphShape",
	56: "ExportAssets",
	57: "ImportAssets",
	58: "EnableDebugger",
	59: "DoInitAction", 	#SWF 6
	64: "EnableDebugger2",
	65: "ScriptLimits",
	66: "SetTabIndex",
	69: "FileAttributes",
	70: "PlaceObject3",
	71: "ImportAssets2",
	76: "SymbolClass",
	77: "MetaData",
	78: "DefineScalingGrid",
	82: "DoABC", 		#SWF 9  AS3
	83: "DefineShape4",
	84: "DefineMorphShape2",
	86: "DefineSceneAndFrameLabelData",
	87: "BinaryData",
	90: "DefineBitsJPEG4"}
	
Actions = {
	0x00: "ActionEnd",
	0x04: "ActionNextFrame",
	0x05: "ActionPreviousFrame",
	0x06: "ActionPlay",
	0x07: "ActionStop",
	0x08: "ActionToggleQuality",
	0x09: "ActionStopSounds",
	0x81: "ActionGotoFrame",
	0x83: "ActionGetURL",
	0x8a: "ActionWaitForFrame",
	0x8b: "ActionSetTarget",
	0x8c: "ActionGoToLabel",
	#SWF4
	0x96: "ActionPush",
	0x17: "ActionPop",
	0x0a: "ActionAdd",
	0x0b: "ActionSubtract",
	0x0c: "ActionMultiple",
	0x0d: "ActionDivide",
	0x0e: "ActionEquals",
	0x0f: "ActionLess",
	0x10: "ActionAnd",
	0x11: "ActionOr",
	0x12: "ActionNot",
	0x13: "ActionStringEquals",
	0x14: "ActionStringLength",
	0x21: "ActionStringAdd",
	0x15: "ActionStringExtract",
	0x29: "ActionStringLess",
	0x31: "ActionMBStringLength",
	0x35: "ActionMBStringExtract",
	0x18: "ActionToInteger",
	0x32: "ActionCharToAscii",
	0x33: "ActionAsciiToChar",
	0x36: "ActionMBCharToAscii",
	0x37: "ActionMBAsciiToChar",
	0x99: "ActionJump",
	0x9d: "ActionIf",
	0x9e: "ActionCall",
	0x1c: "ActionGetVariable",
	0x1d: "ActionSetVariable",
	#MovieControl
	0x9a: "ActionGetURL2",
	0x9f: "ActionGotoFrame2",
	0x20: "ActionSetTarget2",
	0x22: "ActionGetProperty",
	0x23: "ActionSetProperty",
	0x24: "ActionCloneSprite",
	0x25: "ActionRemoveSprite",
	0x27: "ActionStartDrag",
	0x28: "ActionEndDrag",
	0x8d: "ActionWaitForFrame2",
	0x26: "ActionTrace",
	0x34: "ActionGetTime",
	0x30: "ActionRandomNumber",
	#SWF5
	0x3d: "ActionCallFunction"}

#Takes actionCode and data
#Returns a tuple of bytes processed and a list of explanation strings
def action_parser(ac,data):
	retval = []
	if ac == 0x81:
		frame_index = struct.unpack_from('<H', data)[0]
		retval.append("GoTo Frame "+str(frame_index))
	elif ac == 0x83:
		urlstring = data.split('\x00')[0]
		targetstring = data.split('\x00')[1]
		retval.append("Get URL "+str(urlstring) + ' '+str(targetstring))
	elif ac == 0x04:
		retval.append("GoTo Next Frame")
	elif ac == 0x05:
		retval.append("GoTo Prev Frame")
	elif ac == 0x06:
		retval.append("Start Playing")
	elif ac == 0x07:
		retval.append("Stop Playing")
	elif ac == 0x08:
		retval.append("Toggle Quality")
	elif ac == 0x09:
		retval.append("Stop Sound")
	elif ac == 0x8a:
		(frame,skipcount,) = struct.unpack_from("<HB", data)
		retval.append("Wait for Frame "+str(frame)+" or skip "+str(skipcount)+" actions")
	elif ac == 0x96:
		actionType = struct.unpack_from('<B', data)[0]
		if actionType == 0:
			val = data.split('\x00')[0]
		elif actionType == 1:
			val = struct.unpack_from('<f', data[1:])[0]
		elif actionType == 4:
			temp = struct.unpack_from('<B', data[1:])[0]
			val = "Register "+str(temp)
		elif actionType == 5:
			val = struct.unpack_from('<B', data[1:])[0]
			if val == 0:
				val = "False"
			else:
				val = "True"
		elif actionType == 6:
			val = struct.unpack_from('<d', data[1:])[0]
		elif actionType == 7:
			val = struct.unpack_from('<I', data[1:])[0]
		elif actionType == 8:
			val = struct.unpack_from('<B', data[1:])[0]
			val = "Constant8 "+str(val)
		elif actionType == 9:
			val = struct.unpack_from('<H', data[1:])[0]
			val = "Constant16 "+str(val)
		retval.append("Push "+str(val))
	return retval

class ACTIONRECORD():
	def __init__(self,data):
		self.ActionCode = struct.unpack('<B', data)[0]
		if self.ActionCode >= 0x80:
			self.Length = struct.unpack_from('<H', data[1:])[0]
		else:
			self.Length = 0
		if self.ActionCode in Actions.keys():
			self.Name = Actions[self.ActionCode]
			temp = action_parser(self.ActionCode,data[3:])
			
		else:
			self.Name = "Unknown"
		

class RECORDHEADER():
	def __init__(self,ushort):
		temp = bitstring.BitStream(bytes=struct.pack('>H',ushort))
		self.TagType = temp.read(10).uint
		self.TagLength = temp.read(6).uint
		self.length = 0

class DoABC():
	def __init__(self,data):
		self.Flags = data[:4]
		self.Name = data[4:].split('\x00')[0]
		self.ABCData = data[4+len(self.Name)+1:]

class SWFTag():
	def __init__(self,data):
		self.tot_size = 2
		temp = struct.unpack_from('<H', data)[0]
		self.Header = RECORDHEADER(temp)
		
		if self.Header.TagLength == 0x3f:
			self.Header.length = struct.unpack_from('<I', data[2:])[0]
			self.tot_size += 4
		else:
			self.Header.length = self.Header.TagLength

		if self.Header.TagType not in Tags.keys():
			self.TagName = "Unknown"
		else:
			self.TagName = Tags[self.Header.TagType]
		self.TagData = data[self.tot_size:self.tot_size+self.Header.length]
		#Check if it's an action
		if self.Header.TagType in [12]:
			index = 0
			self.Actions = []
			action = ACTIONRECORD(self.TagData)
			while action.ActionCode != 0:
				self.Actions.append(action)
				index += 3
				index += action.Length
				action = ACTIONRECORD(self.TagData[index:])
		#DoABC
		if self.Header.TagType in [82]:
			self.Special = DoABC(self.TagData)

class SWF():
	def __init__(self, data):
		(self.Signature,) = struct.unpack_from('<3s', data)
		self.data = data[3:]
		self.Version = struct.unpack_from('<b', self.data)[0]
		self.data = self.data[1:]
		self.FileLength = struct.unpack_from('<I',self.data)[0]
		self.data = self.data[4:]
		if self.Signature == "CWS":
			self.data = zlib.decompress(self.data)
		temp = bitstring.BitStream(bytes=self.data[:20])
		self.Nbits = temp.read(5).int
		self.rect_size = 5 + (self.Nbits * 4)
		#padding
		self.rect_size += (8 - (self.rect_size % 8))
#Rect
		self.Xmin = temp.read(self.Nbits).int
		self.Xmax = temp.read(self.Nbits).int
		self.Ymin = temp.read(self.Nbits).int
		self.Ymax = temp.read(self.Nbits).int
		self.data = self.data[self.rect_size/8:]
		self.FrameRate = struct.unpack_from('>H', self.data)[0]
		self.data=self.data[2:]
		self.FrameCount = struct.unpack_from('<H', self.data)[0]
		self.data=self.data[2:]
		self.TagList = []
		while len(self.data) > 0:
			nextTag = SWFTag(self.data)
			self.TagList.append(nextTag)
			if nextTag.TagName == "End":
				break
			else:
				sz = nextTag.tot_size + nextTag.Header.length
				self.data = self.data[sz:]
	def getBinaryData(self):
		blobs = []
		for i in range(len(self.TagList)):
			if self.TagList[i].TagName == "BinaryData":
				blobs.append(self.TagList[i].TagData[6:])
		return blobs
	
	def printTagNames(self):
		for tag in self.TagList:
			print(tag.TagName)

	def printDoABC(self):
		for tag in self.TagList:
			if tag.Header.TagType == 82:
				print("Flags: "+binascii.hexlify(tag.Special.Flags))
				print("Name: "+tag.Special.Name)
				print("ABCData: "+binascii.hexlify(tag.Special.ABCData))

	def __str__(self):
		ret = "Signature: "+self.Signature
		ret += "\nVersion: "+str(self.Version)
		ret += "\nFileLength: "+str(self.FileLength)
		ret += "\nWidth(twips): "+str(self.Xmax)
		ret += "\nHeight(twips): "+str(self.Ymax)
		ret += "\nFrameRate: "+str(self.FrameRate)
		ret += "\nFrameCount: "+str(self.FrameCount)

		return ret

data = open(sys.argv[1],'rb').read()
flash = SWF(data=data)
print(flash)
print("\nTags:")
flash.printTagNames()
print("\nDoABC:")
flash.printDoABC()

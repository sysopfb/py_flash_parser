import struct
import sys
import bitstring 
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
	0x04: "ActionNextFrame",
	0x05: "ActionPreviousFrame",
	0x06: "ActionPlay",
	0x07: "ActionStop",
	0x08: "ActionToggleQuality",
	0x81: "ActionGotoFrame",
	0x83: "ActionGetURL"}


class ACTIONRECORD():
	def __init__(self,data):
		self.ActionCode = struct.unpack('<B', data)[0]
		if self.ActionCode >= 0x80:
			self.Length = struct.unpack_from('<H', data[1:])[0]
		else:
			self.Length = 0

class RECORDHEADER():
	def __init__(self,ushort):
		temp = bitstring.BitStream(bytes=struct.pack('>H',ushort))
		self.TagType = temp.read(10).uint
		self.TagLength = temp.read(6).uint
		self.length = 0

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

import struct
import sys
import bitstring 
import zlib

Tags = {0: "End",
	1: "ShowFrame",
	69: "FileAttributes",
	87: "BinaryData"}
	


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

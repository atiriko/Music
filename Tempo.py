class Tempo:
    def __init__(self, bpm, signatureTop=4, signatureBottom=4):
        self.bpm = bpm
        self.tempo1 = [2,2,2,2,2,2,2,2,2,2,2,2,3,3,3,3,3,3,3,3,4,4,5,6,7,0,1]
        self.tempo2 = [2,2,2,2,3,3]
        self.lenghts = [(60 / self.bpm)*4,(60 / self.bpm)*2 ,60 / self.bpm, 60 / self.bpm / 2, 60 / self.bpm / 4, 60 / self.bpm / 8, 60 / self.bpm / 16, 60 / self.bpm / 32, 60 / self.bpm / 64]
        # self.lenghts = {1: 60 / self.bpm, 2: 60 / self.bpm / 2, 4: 60 / self.bpm / 4, 8: 60 / self.bpm / 8, 16: 60 / self.bpm / 16, 32: 60 / self.bpm / 32, 64: 60 / self.bpm / 64}
    
        self.signatureTop = signatureTop
        self.signatureBottom = signatureBottom
        self.bps = 60 / self.bpm
        self.quarter = 1/(1/self.bps)

        self.whole = self.quarter * 4
        self.half  = self.quarter * 2
        self.eighth = self.quarter / 2
        self.sixteenth = self.quarter / 4
        self.thirtysecond = self.quarter / 8
        # self.dot
        self.signature = signatureTop, signatureBottom

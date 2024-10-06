# dataclass notes
class Notes:
    notes= {'z':60,
           's':61,
           'x':62,
           'd':63,
           'c':64,
           'v':65,
           'g':66,
           'b':67,
           'h':68,
           'n':69,
           'j':70,
           'm':71,
           ',':72,
           'l':73,
           '.':74,
           ';':75,
           '/':76,
           'q':72,
           '2':73,
           'w':74,
           '3':75,
           'e':76,
           'r':77,
           '5':78,
           't':79,
           '6':80,
           'y':81,
           '7':82,
           'u':83,
           'i':84,
           '9':85,
           'o':86,
           '0':87,
           'p':88}
    def __init__(self):

        self.C0 = 24
        self.Cs0 = 25
        self.D0 = 26
        self.Ds0 = 27
        self.E0 = 28
        self.F0 = 29
        self.Fs0 = 30
        self.G0 = 31
        self.Gs0 = 32
        self.A0 = 33
        self.As0 = 34
        self.B0 = 35
        self.C = 36
        self.Cs = 37
        self.D = 38
        self.Ds = 39
        self.E = 40
        self.F = 41
        self.Fs = 42
        self.G = 43
        self.Gs = 44
        self.A = 45
        self.As = 46
        self.B = 47
        self.C2 = 48
        self.Cs2 = 49
        self.D2 = 50
        self.Ds2 = 51
        self.E2 = 52
        self.F2 = 53
        self.Fs2 = 54
        self.G2 = 55
        self.Gs2 = 56
        self.A2 = 57
        self.As2 = 58
        self.B2 = 59
        self.C3 = 60
        self.Cs3 = 61
        self.D3 = 62
        self.Ds3 = 63
        self.E3 = 64
        self.F3 = 65
        self.Fs3 = 66
        self.G3 = 67
        self.Gs3 = 68
        self.A3 = 69
        self.As3 = 70
        self.B3 = 71
        self.C4 = 72
        self.Cs4 = 73
        self.D4 = 74
        self.Ds4 = 75
        self.E4 = 76
        self.F4 = 77
        self.Fs4 = 78
        self.G4 = 79
        self.Gs4 = 80
        self.A4 = 81
        self.As4 = 82
        self.B4 = 83
        self.C5 = 84
        self.Cs5 = 85
        self.D5 = 86
        self.Ds5 = 87
        self.E5 = 88
        self.F5 = 89
        self.Fs5 = 90
        self.G5 = 91
        self.Gs5 = 92
        self.A5 = 93
        self.As5 = 94
        self.B5 = 95
        self.C6 = 96
        self.Cs6 = 97
        self.D6 = 98
        self.Ds6 = 99
        self.E6 = 100
        self.F6 = 101
        self.Fs6 = 102
        self.G6 = 103
        self.Gs6 = 104
    
    def noteList(self)->list:
        return [self.C0, self.Cs0, self.D0, self.Ds0, self.E0, self.F0, self.Fs0, self.G0, self.Gs0, self.A0, self.As0, self.B0, self.C, self.Cs, self.D, self.Ds, self.E, self.F, self.Fs, self.G, self.Gs, self.A, self.As, self.B, self.C2, self.Cs2, self.D2, self.Ds2, self.E2, self.F2, self.Fs2, self.G2, self.Gs2, self.A2, self.As2, self.B2, self.C3, self.Cs3, self.D3, self.Ds3, self.E3, self.F3, self.Fs3, self.G3, self.Gs3, self.A3, self.As3, self.B3, self.C4, self.Cs4, self.D4, self.Ds4, self.E4, self.F4, self.Fs4, self.G4, self.Gs4, self.A4, self.As4, self.B4, self.C5, self.Cs5, self.D5, self.Ds5, self.E5, self.F5, self.Fs5, self.G5, self.Gs5, self.A5, self.As5, self.B5, self.C6, self.Cs6, self.D6, self.Ds6, self.E6, self.F6, self.Fs6, self.G6, self.Gs6]
    def __add__(self,other):

        return self
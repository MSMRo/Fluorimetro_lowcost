import ulab

class Integrator:

    def __init__(self, num=10):
        self.num = num
        self.win = ulab.numpy.zeros(num, dtype=ulab.numpy.uint16)
        self.ind = 0

    def update(self,val):
        self.win[self.ind] = val
        self.ind = (self.ind + 1) % self.num
        
    @property
    def value(self):
        return ulab.numpy.sum(self.win)/self.num




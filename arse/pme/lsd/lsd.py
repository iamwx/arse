import tempfile
import os.path
import subprocess
import numpy as np
import matplotlib.pyplot as plt


class Segment(object):
    def __init__(self, p_a, p_b, nfa=None, width=None, precision=None):
        def homogeneous(p):
            if len(p) == 2:
                return np.append(p, [1])
            elif p[2] != 0:
                return np.array(p) / p[2]

        self.p_a = homogeneous(p_a)
        self.p_b = homogeneous(p_b)
        self.nfa = nfa
        self.length = np.linalg.norm(self.p_a - self.p_b)
        self.width = width
        self.precision = precision
        line_ab = np.cross(self.p_a, self.p_b)
        self.line = line_ab / np.linalg.norm(line_ab[:2])

    def plot(self, **kwargs):
        plt.plot([self.p_a[0], self.p_b[0]], [self.p_a[1], self.p_b[1]],
                 **kwargs)


def compute(gray_image, epsilon=0):
    fobj = tempfile.NamedTemporaryFile(suffix='.pgm')
    gray_image.save(fobj.name)

    dir_name = os.path.dirname(__file__)
    exe = '{0}/lsd'.format(dir_name)
    if not os.path.exists(exe):
        sp = subprocess.Popen(['make'], stdout=open(os.devnull, 'wb'),
                              cwd=dir_name)
        sp.wait()

    fobj_txt = tempfile.NamedTemporaryFile(suffix='.txt')
    sp = subprocess.Popen([exe, '-e', str(-epsilon), fobj.name, fobj_txt.name])
    sp.wait()

    segments = []
    for line in fobj_txt:
        l = line.split(' ')
        values = [float(s) for s in l if s and s != '\n']
        segments.append(Segment(values[0:2], values[2:4], width=values[4],
                                precision=values[5], nfa=values[6]))

    return segments


if __name__ == '__main__':
    import PIL.Image
    dir_name = '/Users/mariano/Documents/datasets/YorkUrbanDB/'
    img_name = dir_name + 'P1020839/P1020839.jpg'
    gray_image = PIL.Image.open(img_name).convert('L')
    segments = compute(gray_image, 1)

    plt.figure()
    plt.axis('off')
    plt.imshow(gray_image, cmap='gray', alpha=.5)
    for seg in segments:
        seg.plot(c='g', linewidth=1)

    plt.show()

from __future__ import absolute_import, print_function
import os
import sys
import matplotlib.pyplot as plt
import PIL.Image
import numpy as np
import scipy.io
import functools
import arse.pme.plane as plane
import arse.pme.sampling as sampling
import arse.pme.membership as membership
import arse.pme.acontrario as ac
import arse.test.utils as utils
import arse.test.test_3d as test_3d


class Projector(test_3d.BasePlotter):
    def __init__(self, data, visibility, proj_mat, dirname_in):
        super(Projector, self).__init__(data)
        self.visibility = visibility
        self.proj_mat = proj_mat
        self.dirname_in = dirname_in

    def _project(self, points, k):
        n = points.shape[0]
        data_homogeneous = np.hstack((points, np.ones((n, 1))))
        img_data = data_homogeneous.dot(self.proj_mat[:, :, k].T)
        img_data /= np.atleast_2d(img_data[:, 2]).T
        return img_data

    def special_plot(self, mod_inliers_list, palette):
        if not os.path.exists(self.filename_prefix_out):
            os.mkdir(self.filename_prefix_out)
        self.filename_prefix_out += '/'

        for i, filename in enumerate(os.listdir(self.dirname_in)):
            plt.figure()
            self.inner_plot(mod_inliers_list, palette, filename)
            plt.close()

    def inner_plot(self, mod_inliers_list, palette, filename):
        try:
            idx = int(filename[-7:-4])
            k = idx - 1
        except ValueError:
            return
        if np.any(np.isnan(self.proj_mat[:, :, k])):
            return

        img = PIL.Image.open(self.dirname_in + filename).convert('L')

        plt.imshow(img, cmap='gray')
        plt.axis('off')
        plt.hold(True)

        for (mod, inliers), color in zip(mod_inliers_list, palette):
            inliers = np.squeeze(inliers.toarray())
            visible = np.logical_and(self.visibility[:, k], inliers)
            if visible.sum() < 3:
                continue

            img_data = self._project(self.data[visible, :], k)
            plt.scatter(img_data[:, 0], img_data[:, 1], c='w')

            lower = self.data[visible, :].min(axis=0)
            upper = self.data[visible, :].max(axis=0)
            limits = [(lower[i], upper[i]) for i in range(self.data.shape[1])]
            points = mod.plot_points(limits[0], limits[1], limits[2])
            if not points:
                continue
            points = np.array(points)
            img_points = self._project(points, k)
            plt.fill(img_points[:, 0], img_points[:, 1], color=color, alpha=0.5)

        if self.filename_prefix_out is not None:
            plt.savefig(self.filename_prefix_out + filename + '.pdf', dpi=600)


def run(subsampling=1, inliers_threshold=0.1, run_regular=True):
    log_filename = 'logs/pozzoveggiani_s{0}.txt'.format(subsampling)
    logger = utils.Logger(log_filename)
    sys.stdout = logger

    sigma = 1
    epsilon = 0
    local_ratio = 3

    name = 'PozzoVeggiani'
    dirname = '../data/' + name + '/'

    mat = scipy.io.loadmat(dirname + 'Results.mat')
    data = mat['Points'].T
    proj_mat = mat['Pmat']
    visibility = mat['Visibility']

    # Removing far away points for display
    keep = functools.reduce(np.logical_and, [data[:, 0] > -10, data[:, 0] < 20,
                                             data[:, 2] > 10, data[:, 2] < 45])
    data = data[keep, :]
    visibility = visibility[keep, :]
    # Re-order dimensions and invert vertical direction to get upright data
    data[:, 1] *= -1
    data = np.take(data, [0, 2, 1], axis=1)
    proj_mat[:, 1, :] *= -1
    proj_mat = np.take(proj_mat, [0, 2, 1, 3], axis=1)

    # subsample the input points
    points_considered = np.arange(0, data.shape[0], subsampling)
    data = data[points_considered, :]
    visibility = visibility[points_considered, :]

    n_samples = data.shape[0] * 2
    sampler = sampling.GaussianLocalSampler(sigma, n_samples)
    generator = sampling.ModelGenerator(plane.Plane, data, sampler)
    thresholder = membership.LocalThresholder(inliers_threshold,
                                              ratio=local_ratio)
    min_sample_size = plane.Plane().min_sample_size
    ac_tester = ac.BinomialNFA(epsilon, 1. / local_ratio, min_sample_size)

    projector = Projector(data, visibility, proj_mat, dirname)

    seed = 0
    # seed = np.random.randint(0, np.iinfo(np.uint32).max)
    print('seed:', seed)
    np.random.seed(seed)

    output_prefix = name + '_n{0}'.format(data.shape[0])
    test_3d.test(plane.Plane, data, output_prefix, generator, thresholder,
                 ac_tester, plotter=projector, run_regular=run_regular)

    plt.close('all')

    sys.stdout = logger.stdout
    logger.close()

    return log_filename


def run_all():
    subsampling_list = [10, 5, 2, 1]
    log_filenames = []
    for s_level in subsampling_list:
        fn = run(subsampling=s_level, run_regular=True)
        log_filenames.append(fn)

    log_filenames = ['logs/pozzoveggiani_s10.txt', 'logs/pozzoveggiani_s5.txt',
                     'logs/pozzoveggiani_s2.txt', 'logs/pozzoveggiani_s1.txt']
    test_3d.plot_times(log_filenames, 'pozzoveggiani_times', relative=False)
    test_3d.plot_times(log_filenames, 'pozzoveggiani_times', relative=True)


if __name__ == '__main__':
    run_all()
    plt.show()

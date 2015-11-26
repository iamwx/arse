from __future__ import absolute_import
import comdet.biclustering.compression as compression


class Deflator:

    def __init__(self, array):
        self.array = array
        self._array_lil = None

    def additive_downdate(self, u, v):
        self.array -= u.dot(v)

    def remove_columns(self, idx_cols):
        if self._array_lil is None:
            self._array_lil = self.array.tolil()
        self._array_lil[:, idx_cols] = 0
        self.array = self._array_lil.tocsc()

    def remove_rows(self, idx_rows):
        if self._array_lil is None:
            self._array_lil = self.array.tolil()
        self._array_lil[idx_rows, :] = 0
        self.array = self._array_lil.tocsc()


class L1CompressedDeflator(Deflator):

    def __init__(self, array, n_samples):
        Deflator.__init__(self, array)
        self._compressor = compression.OnlineColumnCompressor(array, n_samples)
        self._inner_compress()

    def _inner_compress(self):
        selection = self._compressor.compress()
        if selection is None:
            try:
                del self.selection
                del self.array_compressed
            except AttributeError:
                pass
        else:
            self.selection = selection
            self.array_compressed = self.array[self.selection, :]

    def additive_downdate(self, u, v):
        super(Deflator, self).additive_downdate(u, v)
        self._compressor.additive_downdate(u, v)
        self._inner_compress()

    def remove_columns(self, idx_cols):
        Deflator.remove_columns(self, idx_cols)
        for i in idx_cols:
            self._compressor.remove_column(i)
        self._inner_compress()

    def remove_rows(self, idx_rows):
        Deflator.remove_rows(self, idx_rows)
        for i in idx_rows:
            self._compressor.remove_row(i)
        self._inner_compress()
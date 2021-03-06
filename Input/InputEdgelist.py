from .InputBase import InputBase
import os
import pandas as pd
import numpy
from scipy.sparse import csr_matrix, coo_matrix
from typing import Optional


class InputEdgelist(InputBase):
    """
    Input adapter for edgelist file without weights.

    """
    def __init__(self, inputfile: str, is_binary: bool, comment: str = '#', has_header: bool = False, delimeter: str = ' '):
        """
        Initialize and check file access.

        :param inputfile: Input file path.
        :param is_binary: Whether the file should be opened in binary mode.
        :param comment: The start character of comment lines in the file.
        :param has_header: Whether the file includes a header line.
        :param delimeter: The character to split for columns.
        """

        self.inputfile = inputfile
        self.is_binary = is_binary
        self.comment = comment
        self.has_header = has_header
        self.delimeter = delimeter
        self.edgelist = None                # type: Optional[pd.DataFrame]
        self.CSR = None                     # type: Optional[csr_matrix]

        # Check file existence
        if not os.access(inputfile, os.R_OK):
            raise IOError('Input file is not accessable!')

    def read_from_file(self) -> None:
        """
        Use ``pandas.read_csv()`` to read from file.

        :return: None.
        """

        print('Reading from edgelist...')
        self.edgelist = pd.read_csv(self.inputfile, delimiter=self.delimeter, header=(1 if self.has_header else None), comment=self.comment).values

    def to_ir(self) -> csr_matrix:
        """
        Reorder the vertex IDs to make them in consequence, and then convert the graph to ``IR``.
        The raw graph (input format) will be destroyed here.

        :return: The graph in ``IR``.
        """

        print('Reordering vertex ID...')
        self.reorder_vertex_id()

        print('Converting to CSR...')
        coo = coo_matrix((self.edgelist[:,0]+1, (self.edgelist[:,0], self.edgelist[:,1])))      # data cannot be zero
        self.CSR = coo.tocsr()

        del self.edgelist       # free memory
        return self.CSR

    """""""""""
    Edgelist specified functions
    """

    def reorder_vertex_id(self):
        """
        Force vertex ID starts from 1 and continuous
        This function should be called at the beginning at :func:`to_ir()`.

        """

        max_vid = numpy.amax(self.edgelist)
        v = numpy.zeros(max_vid+1, dtype=numpy.int64)

        # iterate all elements in edgelist, mark appeared vertex
        for element in numpy.nditer(self.edgelist):
            v[element] = 1
        
        # calculate vertex ID
        v_count = 0
        for i in range(0, max_vid+1):
            if v[i] == 1:
                v[i] = v_count
                v_count += 1

        # update vertex ID
        with numpy.nditer(self.edgelist, op_flags=['readwrite']) as it:
            for x in it:
                x[...] = v[x]
from torch.utils import data
from pathlib import Path
import glob
import os
import six
import json

class DynamicsDataset(object):
    r"""`DynamicsDataset`_ Datasets.

    Publication:

    
    Args:
        root_dir (string): Root directory of dataset where sequence
            folders exist.

    """

    def __init__(self, root_dir):

        super(DynamicsDataset, self).__init__()

        self.root_dir = root_dir

        self.anno_files = sorted(glob.glob(
            os.path.join(root_dir, '*/IR_label.json')))

        self.seq_dirs = [os.path.dirname(f) for f in self.anno_files]


        self.seq_names = [os.path.basename(d) for d in self.seq_dirs]


    def __getitem__(self, index):
        r"""        
        Args:
            index (integer or string): Index or name of a sequence.
        
        Returns:
            tuple: (img_files, anno), where ``img_files`` is a list of
                file names and ``anno`` is a N x 4 (rectangles) numpy array.
        """
        if isinstance(index, six.string_types):
            if not index in self.seq_names:
                raise Exception('Sequence {} not found.'.format(index))
            index = self.seq_names.index(index)

        img_files = sorted(glob.glob(
            os.path.join(self.seq_dirs[index], '*.jpg')))

        with open(self.anno_files[index], 'r') as f:
            label_res = json.load(f)

        # assert len(img_files) == len(label_res['gt_rect'])
        assert len(label_res['gt_rect'][0]) == 4

        return img_files, label_res

    def __len__(self):
        return len(self.seq_names)

    def _filter_files(self, filenames):
        filtered_files = []
        for filename in filenames:
            with open(filename, 'r') as f:
                if f.read().strip() == '':
                    print('Warning: %s is empty.' % filename)
                else:
                    filtered_files.append(filename)

        return filtered_files
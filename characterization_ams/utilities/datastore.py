from __future__ import division, print_function
import os
import sys
import datetime
import numpy as np
from collections import OrderedDict
from scandir import walk
import h5py
import re
import time
import subprocess


class hdf5tools():
    def __init__(self):
        pass

    def types_to_py(self, val):
        if isinstance(val,np.float64):
            if np.isnan(val):val=None
        if isinstance(val,np.ndarray): # assume it is a list and not an numpy array
            if val.ndim == 1:
                val = list(val)
        if isinstance(val,np.bool_):
            val = val == True
        if isinstance(val,bytes):
            val = val.decode('utf-8')
        return val

    def types_to_hdf5(self, val):
        if val is None:val = np.NaN
        return val

    def stats(self, node, array):
        node.attrs['avg'] = np.nanmean(array)
        node.attrs['std'] = np.nanstd(array)
        node.attrs['med'] = np.nanmedian(array)
        node.attrs['min'] = np.nanmin(array)
        node.attrs['max'] = np.nanmax(array)

    def column_header(self, dict_):
        def dtyper(values):
            first_value = next(iter(values))
            if isinstance(first_value, str):
                return np.string_,max(map(len,values))
            elif isinstance(first_value, int):
                return 'i'
            elif hasattr(first_value, 'dtype'):
                return first_value.dtype
            else:
                return 'f'

        dictionary = {}
        if isinstance(dict_, list):
            dict_ = dict(dict_)
        if len(list(dict_.values())[0])==0:
            return 'empty'
        for key, val in dict_.items():
            if not isinstance(key, str):
                key = str(key)

            if not hasattr(val, '__iter__'):
                dictionary[key] = [val]
            else:
                dictionary[key] = val
        try:
            data = np.array(list(zip(*list(dictionary.values()))), dtype = np.dtype( [(key,dtyper(dictionary[key] )) for key in dictionary] ))
        except Exception as e:
            print('h5 compound dataset with mixed types, defaulting to string')
            new_dictionary = {k:list(map(str,v)) for k,v in dictionary.items()}
            data = self.column_header(new_dictionary)
        return data

    def compound_to_array(self, data):
        '''

        Args:
            data: compound data from h5, must not contain strings

        Returns: headerless float array

        '''
        array = np.zeros((data.shape[0],len(self.get_headers(data))), dtype=np.float)
        for index, header in enumerate(self.get_headers(data)):
            array[:,index] = data[header]
        return array

    def get_headers(self, h5dataset):
        return list(h5dataset.dtype.names)

    def find_all_h5(self, dir, include_underscored = False):
        '''

        Args:
            dir                  (str): top directory in which to recursively find all files with the file extensions ".h5"
            include_underscored (bool): if False neglects files and folder starting with an underscore ("_")
        Returns:
            alphabetically sorted filepath list of found h5 files

        '''
        file_list = []
        for dirpath, dirnames, filenames in walk(dir):
            if not "\\_" in dirpath or include_underscored:
                for filename in filenames:
                    if filename.endswith('.h5') and (not filename.startswith("_") or include_underscored):
                        file_list.append(os.path.abspath(os.path.join(dirpath, filename)))
        return sorted(file_list)

    def find(self, measurement, start_directory, filter = None):
        def sorted_nicely(l):
            convert = lambda text: int(text) if text.replace('-','').isdigit() else text
            alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9\-]+)', key) ]
            return sorted(l, key = alphanum_key)

        def action(name, object):
            if filter is None:
                list_.append(start_directory+'/'+name)
            elif re.match(filter, name):
                # if isinstance(object, h5py.Dataset):
                list_.append(start_directory+'/'+name)
        list_= []
        with h5py.File(measurement.path,'a') as h5:
            h5[measurement.__class__.__name__+'/'+start_directory].visititems(action)
        return sorted_nicely(list_)


    def copy_file(self, measurement, newname = None, filter = None, compression = None):
        def sorted_nicely(l):
            convert = lambda text: int(text) if text.replace('-','').isdigit() else text
            alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9\-]+)', key) ]
            return sorted(l, key = alphanum_key)

        def time_estimation(step):
            if step>0:
                total_seconds = (time.time()-start_time)/step*(len(dataset_list))
                return '{:%H:%M:%S} >> {:%H:%M:%S}'.format(datetime.datetime.now(), datetime.datetime.fromtimestamp(start_time + max(0, total_seconds)))
            else:
                return 'started at {:%H:%M:%S}'.format(datetime.datetime.now())

        def action(name, object):
            if isinstance(object, h5py.Dataset):
                dataset_list.append(name)
            else:
                directory_list.append(name)

        directory_list = ['/']
        dataset_list = []
        if newname is None:
            newname = measurement.path[:-3] + '_copied.h5'

        if not '/' in newname and not '\\' in newname:
            newname = os.path.join(os.path.dirname(measurement.path), newname)
        if os.path.abspath(newname)==os.path.abspath(measurement.path):
            print('New name same as old name. Aborting')
            return

        new_file = h5py.File(newname, 'a', libver='latest')
        if compression == 'gzip':
            kwds = {'compression':'gzip'}
        elif compression == 'blosc':
            kwds = {'shuffle' : False, 'compression' : 32001, 'compression_opts' :(0, 0, 0, 0, 9, 1, 1)}
        elif compression == 'szip':
            kwds = {'compression':'szip', 'compression_opts':5}
        elif compression == 'lzf':
            kwds = {'compression':'lzf'}
        else:
            kwds = {}

        with h5py.File(measurement.path,'r', libver='latest') as h5:
            h5.visititems(action)

            for directory in directory_list:
                new_file.require_group(directory)
                for key,val in h5[directory].attrs.items():
                    new_file[directory].attrs[key] = val

            start_time = time.time()
            for i, dataset in enumerate(sorted_nicely(dataset_list)):
                if not filter is None:
                    if re.match(filter, dataset):
                        print('>>>', dataset)
                        continue

                sys.stdout.write('\r{} {}'.format(time_estimation(i), dataset))
                # if re.match('.*/avg$', dataset):
                #     new_file.create_dataset(dataset, data=h5[dataset][()].astype(np.float32), **kwds)
                if len(h5[dataset].dims)>0:
                    new_file.create_dataset(dataset, data=h5[dataset][()], **kwds)
                else:
                    new_file.create_dataset(dataset, data=h5[dataset][()])

                for key,val in h5[dataset].attrs.items():
                    new_file[dataset].attrs[key] = val
            sys.stdout.write('\r')
        new_file.close()



    def _command(self, command, verbose = True):
        p = subprocess.Popen(command, shell = True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        lines = []
        for line in iter(p.stdout.readline, b''):
            text = line.decode('utf-8').replace('\\r\\n','')
            if verbose:
                print(text,)
            lines.append(text)
        p.stdout.close()
        p.wait()
        error =p.stderr.read().decode('utf-8').replace('\\r\\n','\n')
        if len(error)>0:
            print(command)
            raise(Exception(error))

        return '\n'.join(lines)

    def clear_flag(self, path):
        '''
        The h5clear tool can either clear the status_flags field in the superblock of the file or close a metadata cache image in the specified file.
        With the implementation of file locking, the library uses the status_flags field in the superblock to mark a file as in writing or SWMR writing mode when a file is opened. The library will clear this field when the file closes.

        However, a situation may occur where an open file is closed without going through the normal library file closing procedure, and this field will not be cleared as a result. An example would be if an application program crashed. This situation will prevent a user from opening the file. The h5clear tool will clear the status_flags field, and the user can then open the file.

        When used to close a metadata cache image, h5clear will open the supplied HDF5 file in Read-Write (R/W) mode, check to see if it contains a cache image, and then close it. If the file does not contain a cache image, h5clear will generate a warning message to that effect.
        '''
        command = '"{}" -s "{}"'.format(os.path.join(os.path.dirname(sys.executable), r'Library\bin\h5clear.exe'), path)
        self._command(command)

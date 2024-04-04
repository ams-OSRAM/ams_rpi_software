import h5py

class H5ImageWriter:
    # Initialize the H5ImageWriter class
    def __init__(self, filename, dataset_name):
        # Store the filename and dataset name as instance variables
        self.filename = filename
        self.dataset_name = dataset_name

    # Write a single image to the HDF5 file
    def write_image(self, image):
        # Open the HDF5 file in write mode
        with h5py.File(self.filename, 'w') as f:
            # Create a dataset with the specified name and write the image data to it
            dataset = f.create_dataset(self.dataset_name, data=image)

    # Write metadata to the HDF5 file
    def write_metadata(self, metadata, parent_path=''):
        # Open the HDF5 file in read/write mode
        with h5py.File(self.filename, 'r+') as f:
            # Iterate over the metadata dictionary
            for key, value in metadata.items():
                # Create the path to the metadata
                path = parent_path + '/' + key
                # If the value is a dictionary, recursively traverse it
                if isinstance(value, dict):
                    self.write_metadata(value, path)
                else:
                    # Otherwise, write the metadata to the file
                    dataset = f[path]
                    dataset.attrs['metadata'] = value

    # Get the maximum level of metadata nesting
    def get_metadata_nesting_level(self, path=''):
        # Open the HDF5 file in read mode
        with h5py.File(self.filename, 'r') as f:
            # Get the dataset at the specified path
            dataset = f[path]
            # Initialize the maximum nesting level to 0
            max_level = 0
            # Iterate over the keys in the dataset
            for key in dataset.keys():
                # Recursively traverse the metadata to find the maximum level of nesting
                level = self.get_metadata_nesting_level(path + '/' + key)
                max_level = max(max_level, level)
            # Return the maximum nesting level + 1 (to account for the current level)
            return max_level + 1

class BaseH5ImageWriter(H5ImageWriter):
    # Initialize the BaseH5ImageWriter class
    def __init__(self, filename, dataset_name):
        # Call the __init__ method of the H5ImageWriter superclass
        super().__init__(filename, dataset_name)

    # Write multiple images to the HDF5 file
    def write_images(self, images):
        # Iterate over the images
        for image in images:
            # Call the write_image method of the H5ImageWriter superclass for each image
            self.write_image(image)
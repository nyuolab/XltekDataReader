# NatusDatabaseExtraction
## Required packages
numpy, opencv-python
## Intro to NeuroWorks data format
The data in neuroworks EEG databases consists of a few core components:
1. Patient information file (`.eeg` files) contains various data about the patient and study,
2. Raw data file (`.erd` files) contains the raw EEG sequences recorded,
3. Note data file (`.ent` files) contains notes, comments and annotations of the study.

Usually, each neuroworks file has two parts: A generic header, and the file entries. The generic header is shared among these files (which includes information like patient name and study id), and file entries are speicifc to their function. Each of these parts can have various versions, and their version is termed "schema". The version of the generic header is refered to as base schema, and the version of the file entries are called file schema. Each base schema or file schema specifies a slightly different way of storing and loading information. The behavior of this package can be altered to fit many different schemas, provided you create or edit the data templates corretly. Please consult later sections for how to do this.

## How to use this package
Each folder of NeuroWorks data consists of only 1 `.eeg` file, only 1 `.ent` file, and multiple `.erd` files. The recorded time series are scattered in these `.erd` files. This package will first scan the entire folder and find these different files, load them individually, and finally combine the information in them. To load all files in a directory called `DIR_NAME`, simply run:
```
from file_loader.xltek_loader import XltekLoader

loader = XltekLoader(DIR_NAME)
ret = loader.load()
```
The returned value `ret` will be a dictionary of this structure:
```
{
  'StudyInfo': A dictionary of metadata,
  'EEGData': Numpy array of shape (num_sensors+1 x T), EEG data, the last channel is the filetime for that recording where mising values indicated by np.NAN,
  'ChannelNames': List of string, name of each channel in EEGData,
  'Notes': Dictionary with integer key, each key-value pair is the (sample stamp-note dictionary) pair,
  'FrameAndFiletime': A 2-tuple. The first element is a list of video filenames, and the second element is an int numpy array of size `t` indicating the filetime of each frame,
  'FiletimeStampConversion': A 2-tuple. The first element is a list of filetimes, and the second element is a list of sample stamps. Used to synchronize filetime and framestamp. Due to having only a small number of filetime-samplestamp pairs, interpolation is necessary to create a dense map of frames.
}
```

Note that the video and EEG data are likely collected with different sampling frequency, therefore you can't match them exactly. The recommended way is to match them using the filetime stamp associated with each video frame and eeg data.

## Using data templates
### What are data templates
Data template is a way for people to use this software in a flexible way. Data template is a language that you can use to describe the format of your neuroworks (or similar format) files. This language can be understood by our code and our code will automatically load the files. 
### Json files
For this project, data templates are all json files. [Here](https://en.wikipedia.org/wiki/JSON?oldformat=true) is a more in-depth introduction on json. A json file looks something like this:
```
{
  "Item_A": "Attribute 1",
  "Item_B": {
    "Attribute 1": 1,
    "Attribute 2": 2
  }
}
```
If you are familliar with python, you will immediately recognize this as a nested dictionary -- this is exactly what json files are. This is a very human-readable way of describing hierarchical information. 
### Basic usage
Our code will use the data template you provided as a guide for reading data from neuroworks database. Here is an example, let's go through it step by step.
```
{
  "Struct 1": {
    "H": ["int", 1],
    "W": ["int", 3]
  }
}
```
This data template will tell our code that the data has a field called "struct 1", and it has 2 fields. The "H" field is of integer type and length 1, and the "W" field is of integer type and length 3. Unfortunately our code only support at most 2 levels of nested dictionaries. We might update this in the future.

Since most of the files in neuroworks format has a shared generic file header and a type-specific file header, this two parts are separated. The generic header information is stored in `./data_templates/` directory, and the specific file headers of their file schema are stored in directories like `./data_templates/eeg/file_schema_3/`.

### Datatemplates without file schema
If the file you are loading doesn't have a base schema, then we assume it doesn't have a file schema either. In this case, assuming the file type is called `sample_file`, just place its data template file in the `./project_root/data_templates/sample_file/` directory. When constructing the class, use `base_schema=-1` in the super class constructor call. For an example, see the `.vtc` file in `./project_root/file_loader/file_types/vtc_file.py`.

### Supported reading formats
The basic fields that are readable by our code are listed here:
1. "i", integer. 4 bytes. Use like this: `["i", num_reads]`.
2. "h", half. 2 bytes. Use like this: `["h", num_reads]`.
3. "string", string. Can be arbitrarily long, but you can also specify how long it is. Use like: `["string", max_length, null_terminated]`.
4. "key_tree", key tree. Basically a tree-like dictionary structure. We parse it for you. Use like: `["key_tree", max_length, null_terminated]`.

### Special data fields
If the capability of our code is not enough to accomodate for a new field (e.g. due to the file structure being too dynamic), you can write a custom field into the json file, and this will direct our code to go to your own code. Simply use "special:xxx" as the special field's name.

### Requirements
You might want to check the values of some fields to validate the files' integrity. We provide some basic forms of validation. With exactly the same structure as the data format descriptions, simply add new entries at the end with your required value. These added entries need to begin with "requirements:", and all the fields being checked need to have identical names. An example:
```
{
  "Struct 1": {
    "H": ["int", 1],
    "W": ["int", 3]
  },
  "requirement:Struct 1": {
    "H": 4,
    "W": [0, 1, 2]
  }
}
```
### Checkpoints
Sometimes you might make typos in the data template. To help check for this, you can mannually input the file reading cursor offset as a way to reduce error. Simply add "read_checkpoint" before any arbitrary name (but the position matters). An example:
```
{
  "generic_file_header": {
    ...
  },
  "read_checkpoint_1": 352
}
```
This code will make sure the curosr is at byte 352 after reading the generic file header.
### Repeats
One of the most useful feature is the repeat. Sometimes your file has some type of repeating structure. For example, maybe it's a packet of data that has 2 different integers. Instead of writing a special field reader, you can specify the repeat in data templates. But currently the repeat will last strictly until the end of file, and thus has to be the last field to be loaded. Simply add "repeat:" before any field, and the code will automatically load repeating units of data until EOF. The files will be loaded as a list in each field.
#### Conditional repeats
Sometimes the repeating units have dependencies on each other. For example, maybe the first byte tells you how long to load. Conditional repeat feature allows you to write simple conditional relations in data templates. Simply replace the num_read field with any python evaluatable string. All previously loaded values will be available. An example:
```
{
  "repeat:data_packet": {
    "size_num_bytes": ["i", 1],
    "text_data": ["string", "size_num_bytes-4"]
  }
}
```
# XltekDataReader

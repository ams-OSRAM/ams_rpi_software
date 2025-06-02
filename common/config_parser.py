import pathlib
import csv

class ConfigParser:
    def __init__(self):
        # Placeholder init function
        self.reg_seq = []
    def parse_file(self, filepath):
        reg_seq = []
        with open(filepath, "r") as f:
            for line in f:
                try:
                    values = line.split()
                    if len(values) > 0:
                        if values[0] != '#' and values[0].lower()=='write':
                            # Create a temporary lower-case line for matching
                            values_lower = [item.lower() for item in values]
                            # Find where the keyword "write" starts in the line
                            write_index = values_lower.index('write')
                            # Parse: write val to addr
                            val_index = write_index + 1
                            addr_index = write_index + 3
                            if ('x' in values[addr_index]) or ('X' in values[addr_index]):
                                addr =  (int(values[addr_index],16))
                            else:
                                addr = (int(values[addr_index],10))
                            if ('x' in values[val_index]) or ('X' in values[val_index]):
                                val =  (int(values[val_index],16))
                            else:
                                val =  (int(values[val_index],10))
                            reg_seq.append((addr, val))
                except IndexError as e:
                    print(e)
                else:
                    pass
        self.reg_seq=reg_seq
        return reg_seq
        
    def parse_csv(self, filepath):
        reg_seq = []
        with open(filepath,newline='') as csvfile:
            spamreader = csv.reader(csvfile, delimiter=',')
            for values in spamreader:
                val_index =  1
                addr_index = 0
                if ('x' in values[addr_index]) or ('X' in values[addr_index]):
                    addr =  (int(values[addr_index],16))
                else:
                    addr = (int(values[addr_index],10))
                if ('x' in values[val_index]) or ('X' in values[val_index]):
                    val =  (int(values[val_index],16))
                else:
                    val =  (int(values[val_index],10))
                reg_seq.append((addr, val))
               
        self.reg_seq=reg_seq
        return reg_seq

import io
import sys
import argparse
import os
import time
import numpy as np

def convert(input, output, w, h, bpp):
    # Open input file for reading
    with open(input, "rb") as f:
        numpy_data = np.fromfile(f,dtype=np.uint8)
        size = int(w * h * bpp / 8)
        if size == numpy_data.shape[0]:
            print(f"Input check passed. File size of {size} Bytes is correct");
        else:
            print(f"Input check failed. Expecting {size} Byte but file is {numpy_data.shape[0]} Bytes")
            return -1
    # Create 16-bit per pixel container for the image
    container = np.empty([w*h], dtype=np.uint16)
    # Two 12 bit pixels (A and B) are packed into 3 bytes
    #  byte 1   byte 2   byte 3
    # AAAAAAAA BBBBBBBB AAAABBBB
    # byte 1 and byte 2 each contains 8 MSB of pixel A and B
    # byte 3 contains 4 LSB of pixel A and B
    # Create a pointer to byte 1, which contains bit 4 to bit 11 of pixel A
    pA_b4_b11 = numpy_data[::3]
    # Create a pointer to byte 2, which contains bit 4 to bit 11 of pixel B
    pB_b4_b11 = numpy_data[1::3]
    # Create a pointer to byte 3, which contains bit 0 to bit 3 of pixel A and pixel B
    pA_pB_lsb = numpy_data[2::3]
    # Copy byte 1 and byte 2 to the 16-bit container, and shift the MSB.
    container[::2] = pA_b4_b11[::].astype(np.uint16) << 4
    container[1::2] = pB_b4_b11[::].astype(np.uint16) << 4
    # Obtain the LSB of pixel A and B and add to the container.
    for byte in range(2):
        container[byte::2] |= ((pA_pB_lsb[::] >> (2 - byte) * 4) & 0b1111)
    # Open output file and write a PGM header
    with open(output, 'w') as f:
        f.write("P5\r")
        f.write(f"{str(w)} ")
        f.write(f"{str(h)}\r")
        f.write(f"{2**bpp-1}\r")
    # Swap bytes endianess, as pgm uses big endian and ImageJ as well.
    container.newbyteorder().byteswap(inplace=True)
    # Write the container to file
    with open(output, 'ab') as f:
        f.write(container)
    print(f"Output converted image to file {output}.");


if __name__ == "__main__":
    # Argument handling
    ap = argparse.ArgumentParser(description='Convert 12 bit pack RAW to 16 bit PGM.')
    ap.add_argument('-input', type=str, required=True, help='input: input image file.')
    ap.add_argument('-width', type=int, required=True, help='width: width of input image.')
    ap.add_argument('-height', type=int, required=True, help='height: height of input image.')
 
    args = vars(ap.parse_args())
    # Process -input
    arg_input = args['input'] 
    if not os.path.exists(arg_input) :
        print(f"ERROR: -input does not exist ({arg_input})")
        exit(-1)
    # Process -width
    arg_width = args['width']
    # Process -height
    arg_height = args['height']

    input = arg_input
    output = arg_input+".pgm"
    w = arg_width
    h = arg_height
    bpp = 12
    assert(bpp == 12), f"Only 12 bits per pixel input is supported."
    convert(input, output, w, h, bpp)


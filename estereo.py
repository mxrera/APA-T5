"""
Gerard Cots i Escude i Joel Joan Morera
"""
import struct as st
import matplotlib.pyplot as plt

def read_wave(filename: str) -> dict | dict:
    """
    Reads a WAVE file and returns two dictionaries with the file sub-chunks.

    See http://soundfile.sapp.org/doc/WaveFormat/

    Args:
        filename: name of the file

    Returns:
        - Header:
            - ChunkID
            - ChunkSize
            - Format
            - Subchunk1ID
            - SubChunk1Size
            - AudioFormat
            - NumChannels
            - SampleRate
            - ByteRate
            - BlockAlign
            - BitsPerSample
        - Data:
            - SubChunk2ID
            - SubChunk2Size
            - data
    """
    header = {}
    data = {}
    with open(filename , "rb") as f:
        # RIFF chunk descriptor
        format = "<4sI4s"
        buffer = f.read(st.calcsize(format))
        header["ChunkID"], header["ChunkSize"], header["Format"] = st.unpack(format, buffer)
        
        position = st.calcsize(format)
        f.seek(position)

        # Check file format    
        if header["Format"] != b"WAVE":
            raise ValueError(f"File '{filename}' is not a WAVE file")

        # fmt subchunk
        format = "<4sI2H2I2H"
        buffer = f.read(st.calcsize(format))
        (
            header["SubChunk1ID"],
            header["SubChunk1Size"],
            header["AudioFormat"],
            header["NumChannels"],
            header["SampleRate"],
            header["ByteRate"],
            header["BlockAlign"],
            header["BitsPerSample"]
        ) = st.unpack(format, buffer)
        
        position += st.calcsize(format)
        f.seek(position)

        # data subchunk
        format = "<4sI"
        buffer = f.read(st.calcsize(format))
        data["SubChunk2ID"], data["SubChunk2Size"] = st.unpack(format, buffer)
        
        position += st.calcsize(format)
        f.seek(position)

        # data
        buffer = f.read()
        data["data"] = [int(sample[0]) for sample in st.iter_unpack("<h", buffer)]

    return header, data

def write_wave(filename: str, header: dict, data: dict):
    """
    Escriu un fitxer de so amb les dades i el header donats.
    """
    if header["Format"] != b"WAVE":
        raise ValueError(f"File {filename} is not a WAVE file")
        
    with open(filename, "wb") as f:
        # RIFF chunk descriptor
        format = "<4sI4s"
        buffer = st.pack(format, header["ChunkID"], header["ChunkSize"], header["Format"])
        f.write(buffer)

        # fmt subchunk
        format = "<4sI2H2I2H"
        buffer = st.pack(
            format,
            header["SubChunk1ID"],
            header["SubChunk1Size"],
            header["AudioFormat"],
            header["NumChannels"],
            header["SampleRate"],
            header["ByteRate"],
            header["BlockAlign"],
            header["BitsPerSample"]
        )
        f.write(buffer)

        # data subchunk
        format = "<4sI"
        buffer = st.pack(format, data["SubChunk2ID"], data["SubChunk2Size"])
        f.write(buffer)

        # data
        format = f"<{len(data['data'])}h"
        buffer = st.pack(format, *data["data"])
        f.write(buffer)

def estereo2mono(ficEste, ficMono, canal=2):
    header, data = read_wave(ficEste)
    if header["NumChannels"] != 2:
        raise ValueError(f"File '{ficEste}' is not an estereo file")
    
    # Mono header
    header["NumChannels"] = 1
    header["ByteRate"] = header["SampleRate"] * header["NumChannels"] * header["BitsPerSample"]//8
    header["BlockAlign"] = header["NumChannels"] * header["BitsPerSample"]//8

    # Define data to be saved
    left_channel, right_channel = data["data"][::2], data["data"][1::2]
    mono_data = {
        "SubChunk2ID": b"data",
        "SubChunk2Size": 0,
        "data": []
    }

    if canal == 0:
        mono_data["data"] = left_channel
    elif canal == 1:
        mono_data["data"] = right_channel
    elif canal == 2:
        mono_data["data"] = [(left_sample + right_sample) // 2 for left_sample, right_sample in zip(left_channel, right_channel)]
    elif canal == 3:
        mono_data["data"] = [(left_sample - right_sample) // 2 for left_sample, right_sample in zip(left_channel, right_channel)]
    else:
        raise ValueError(f"Channel must be a number between 0 and 3, both included.")
    
    mono_data["SubChunk2Size"] = len(mono_data["data"]) * header["NumChannels"] * header["BitsPerSample"]//8

    write_wave(ficMono, header, mono_data)

def mono2estereo(ficIzq: str, ficDer: str, ficEste: str):
    left_header, left_data = read_wave(ficIzq)    
    if left_header["NumChannels"] != 1:
        raise ValueError(f"File '{ficIzq}' is not a mono file")
    
    right_header, right_data = read_wave(ficDer)
    if right_header["NumChannels"] != 1:
        raise ValueError(f"File '{ficDer}' is not a mono file")
    
    # Estereo header
    header = left_header
    header["NumChannels"] = 2
    header["ByteRate"] = header["SampleRate"] * header["NumChannels"] * header["BitsPerSample"]//8
    header["BlockAlign"] = header["NumChannels"] * header["BitsPerSample"]//8

    # Define data to be saved
    data = {
        "SubChunk2ID": b"data",
        "SubChunk2Size": 0,
        "data": []
    }
    data["data"] = right_data["data"] + left_data["data"] # Total data length is the sum of both mono files
    data["data"][::2] = left_data["data"]
    data["data"][1::2] = right_data["data"]
    data["SubChunk2Size"] = len(left_data["data"]) * header["NumChannels"] * header["BitsPerSample"]//8

    write_wave(ficEste, header, data)

def codEstereo(ficEste: str, ficCod: str):
    pass

def decEstereo(ficCod: str, ficEste: str):
    pass
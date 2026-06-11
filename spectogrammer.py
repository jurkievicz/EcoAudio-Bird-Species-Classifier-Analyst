import librosa
import numpy as np
from audiomentations import Compose, AddGaussianNoise, TimeStretch, PitchShift, Gain


#from wav to a normalized 2D matrix
def make_melspec(audio_file_path):
    y, sr = librosa.load(audio_file_path, sr=22050, mono=True)
    spectogram = librosa.feature.melspectrogram(y, sr=22050, n_mels=128, n_fft=2048, hop_length=512)
    log_spectogram = librosa.power_to_db(spectogram, ref=np.max)

    mean = np.mean(log_spectogram)
    std_dev = np.std(log_spectogram)
    normalized_spectogram = (log_spectogram - mean) / (std_dev + 1e-8)

    return normalized_spectogram


#making the same length samples
def window_spectrogtram(spectrogram_matrix):
    window_width = 216
    hop_size = window_width // 2
    final_window = []

    total_columns = spectrogram_matrix.shape[1]

    for start_col in range(0, (total_columns - window_width) + 1, hop_size):
        end_col = start_col + window_width
        chuck = spectrogram_matrix[:, start_col:end_col]

        final_window.append(chuck)

    return final_window

#adding noise, time stretch, pitch shifts and volume gain for model to train on non-perfect data
def create_augmentation_pipeline():
    pipeline = Compose([
        AddGaussianNoise(min_amplitude=0.001, max_amplitude=0.015, p=0.5),
        TimeStretch(min_rate=0.9, max_rate=1.1, p=0.5),
        PitchShift(min_semitones=-2, max_semitones=2, p=0.5),
        Gain(min_gain_db=-6, max_gain_db=6, p=0.5)
    ])

    return pipeline




































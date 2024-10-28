# Music Composer

## Project Description

The Music Composer project is a Python-based application designed to assist users in creating and manipulating musical compositions. The project leverages the Pygame library for its graphical interface and integrates MIDI functionalities to handle musical notes and sequences.

### Key Features

- **Melody Generation**: Automatically generate melodies based on musical progressions, keys, and scales.
- **Event Scheduling**: Schedule musical events such as notes and rhythms to create complex compositions.
- **MIDI Integration**: Export compositions as MIDI files for further use in digital audio workstations (DAWs).

### Core Functionality

#### Melody Generation

The [`generateMelody`]function is a core component of the project. It generates a melody based on a given chord progression, key, and scale. The function works as follows:

1. **Initialization**: Sets up the melody channel and initializes lists to store melody notes and lengths.
2. **Melody Creation**: Iterates over 64 bars to create a melody. For every 4th bar, it uses the chord progression to determine the note. For other bars, it randomly selects notes from the scale.
3. **Note Lengths**: For each bar, it assigns random note lengths (whole, half, quarter, eighth) to the melody notes.

#### Event Scheduling

The project includes an event scheduler to manage the timing and sequencing of musical events. This allows for precise control over when notes are played, ensuring that the generated melodies and rhythms are synchronized correctly.

### Usage

1. **Run the Main Script**: Execute the main script to launch the application.
    ```sh
    python main.py
    ```

2. **Generate Melodies**: Use the [`generateMelody`] function to create melodies based on your desired musical parameters.

3. **Export MIDI**: Save your compositions as MIDI files for use in other music production software.

### Project Structure

- 

main.py

: Entry point of the application.
- 

Song.py

: Contains the melody generation and event scheduling logic.
- 

UIGPT.py

: Manages the user interface and event handling.
- 

Scheduler.py

: Handles the scheduling of musical events.
- 

Record.py

: Manages recording functionality.
- 

Freeplay.py

: Implements freeplay mode.
- 


## Features

- **Piano Roll Interface**: Visual interface for composing music.
- **Recording**: Record your compositions.
- **MIDI File Export**: Save your compositions as MIDI files.
- **Freeplay Mode**: Play and record music freely.

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/yourusername/music-composer.git
    cd music-composer
    ```

2. Install the required dependencies:
    ```sh
    pip install -r requirements.txt
    ```

3. Ensure you have the necessary assets in the `Assets/` directory:
    - `music.png`
    - `export.sf2`
    - `LAYLA.MID`

## Usage

1. Run the main script:
    ```sh
    python main.py
    ```

2. Follow the on-screen instructions to interact with the application:
    - Press `r` to restart.
    - Press `s` to save.
    - Press `f` to enter freeplay mode.
    - Press `Ctrl+C` to exit.

## Project Structure

- `main.py`: Entry point of the application.
- `UIGPT.py`: Contains the UI logic and event handling.
- `Scheduler.py`: Handles scheduling of musical notes.
- `Record.py`: Manages recording functionality.
- `Freeplay.py`: Implements freeplay mode.
- `Assets/`: Contains necessary assets like images and sound fonts.
- `recordings/`: Directory where recordings are saved.

## Contributing

1. Fork the repository.
2. Create a new branch (`git checkout -b feature-branch`).
3. Make your changes.
4. Commit your changes (`git commit -am 'Add new feature'`).
5. Push to the branch (`git push origin feature-branch`).
6. Create a new Pull Request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgements

- [Pygame](https://www.pygame.org/) for the game development library.
- [Mido](https://mido.readthedocs.io/) for MIDI file handling.
- [PySide6](https://pypi.org/project/PySide6/) for the GUI components.

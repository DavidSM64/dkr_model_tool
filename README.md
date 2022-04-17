# dkr_model_tool

This is a simple tool that can be used to convert 3D level models to/from the DKR binary format.

Note: This is still heavly work-in-progress, and is probably not ready to be used by anyone just yet. Feel free to look at the code to see how things work.

## Requirements

I'm not sure of the minimum version of python you need, but for reference I use python 3.8.5

### Packages

* Pillow - For loading images
* PyOpenGL - For the preview window
* PyQt5 - For the preview window
* numpy - For the preview window

`pip install Pillow PyOpenGL PyQt5 numpy`

## Converting

`python dkr_model_tool.py <import file path> -o <export file path>`

### Supported import file formats

* DKR level binary file (.bin/.cbin)
* Wavefront OBJ (.obj)

### Supported export file formats

* DKR level binary file (.bin/.cbin)
* Wavefront OBJ (.obj)

Note: If you have the DKR decomp setup on your computer, then you should link it by creating a file called `path-to-decomp.txt` in the root directory. If this is not set, then you may see temporary textures being used instead of vanilla textures.

## Preview Window

`python dkr_model_tool.py <import file path>`

Allows you to view what the level should look like in-game. Should work with any model that can be imported.

### Controls

* W,A,S,D keys to move
* Hold left mouse button, and then move mouse to change camera rotation.
* You can use the mouse's scroll wheel to move forward/backward too. 

![](https://i.imgur.com/MPex6dr.png)

## License

MIT License

Copyright (c) 2022 David Benepe

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

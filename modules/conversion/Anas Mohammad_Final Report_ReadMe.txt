Final Progress Report: SVS and DICOM Image Workflow
Throughout this project, I focused on building a flexible pipeline to process and analyze digital pathology slides—specifically in SVS and DICOM formats. My work spanned a wide range of tasks, including collecting whole-slide image (WSI) data, extracting embedded metadata and labels, converting between file types, accessing individual layers of multi-resolution slides, and selectively saving specific layers as JPEGs for downstream tasks like inspection or redaction.

This required a deep understanding of medical image formats, how WSIs are structured internally, and how to navigate their hierarchical (pyramidal) resolution levels using tools like OpenSlide, PyVips, and Tifffile. My efforts involved numerous iterations, problem-solving around software limitations, and ultimately building scripts that could reliably automate core parts of this workflow.

1. Data Collection and Format Handling
The first step was obtaining pathology slides in .svs and .dcm formats. I learned quickly that .svs (used by Aperio scanners) and .dcm (DICOM for digital pathology) are fundamentally different even though they may contain similar content.

SVS files are actually specialized multi-page TIFF containers. Each page (or more accurately, SubIFD) contains a different resolution of the same slide. The highest resolution is stored at level 0, and each subsequent level contains a downsampled version used for faster navigation and zooming.

DICOM WSIs, while sometimes single-frame, can also be stored in multi-frame format. Each frame could represent a tile, a depth layer, or a resolution level. Handling them correctly depends heavily on metadata and expected structure.

Understanding how these formats stored image data was essential before I could begin manipulating or extracting anything from them.

2. Label Extraction and Metadata Access
One of the intermediate goals was to extract labels or macros embedded in SVS files. In Aperio slides, label images or thumbnail previews are typically stored as additional sub-resolutions or metadata-associated pages. My challenge was not only identifying which pages contained meaningful content, but also accessing and exporting them programmatically.

To do this, I used both:

OpenSlide, which provides clear access to known sub-resolutions via .level_dimensions, .read_region, and .associated_images.

PyVips, which supports low-level access through subifd= or page= arguments, although this route required more experimentation due to inconsistent behavior across SVS files.

I was able to extract these label or macro images as standard RGB arrays and save them using OpenCV, making them easy to inspect or archive.

3. Layer Extraction Across Pyramid Levels
One of the most technically challenging and rewarding aspects of the project was reading and manipulating multiple resolution levels of WSIs. SVS files don’t just contain one image—they store a pyramid of images, each corresponding to a different zoom level. Accessing and handling these properly was essential.

Using OpenSlide, I loaded each resolution level individually using read_region() while looping over level_count. I extracted these regions as RGBA PIL images, converted them to NumPy arrays, and optionally saved them to disk.

I also built logic to:

Scale annotation coordinates according to the resolution level.

Track tile sizes and image dimensions across levels.

Handle color channel conversions, from RGBA to RGB and BGR (for OpenCV compatibility).

This level of control allowed me to process each layer independently, which was crucial when I needed to save specific resolution layers (e.g., for JPEG generation or redaction).

4. File Type Conversion and Output Formats
Once I had a working system to load and extract data from .svs and .dcm files, I worked on converting this data to more accessible formats:

SVS to JPEG: I built scripts to extract the top three layers from an SVS, apply simple image operations, and save them as .jpg files. This was especially useful for fast visual verification, sharing, and debugging.

DICOM to JPEG: I created a lightweight tool using pydicom and cv2 to convert single-frame .dcm images to JPEGs. I included logic to normalize 16-bit grayscale DICOM data to 8-bit JPEG format, which is critical for compatibility.

SVS to Pyramidal TIFF: When redacting or modifying content, I had to regenerate a valid pyramidal file. While I couldn’t replicate Aperio’s SVS tags exactly, I used tifffile.TiffWriter to create a multi-resolution .tif that mimicked the structure, enabling compatibility with WSI viewers like QuPath or ASAP. These TIFFs were saved with appropriate tile sizes, compression, and resolution hierarchy.

In each of these conversions, I had to account for format-specific quirks (e.g., color space, compression support, or file size concerns) and validate the output in multiple tools.

5. Redaction as a JPEG-Specific Use Case
While not the central goal of the project, I also implemented redaction tools that blacked out specific areas of a slide. These edits were applied to the top three layers of an SVS (or a single DICOM frame), and the result was saved exclusively as JPEGs.

6. Technical Challenges and Debugging
There were many technical difficulties along the way:

Library Issues: Installing pyvips on Windows required setting up the correct DLL paths, and I had to experiment with multiple builds to access basic layout functionality. Some features like layout="svs" were missing entirely.

Imagecodecs & Compression: JPEG compression in TiffWriter initially failed due to missing jpeg_encode support. I had to either upgrade imagecodecs, remove compression altogether, or switch to alternatives like LZW.

API Inconsistencies: Functions like dzsave() or tiffsave() accepted slightly different parameters depending on the platform and version. I often had to rewrite portions of code due to minor argument mismatches (e.g., jpegquality vs compressionargs).

Closed File Handles: In OpenSlide, attempting to access level_downsamples after calling slide.close() caused critical errors. Fixing this required careful ordering of operations and managing state correctly.

Despite these issues, I worked through each one—debugging call stacks, checking function documentation, and iteratively testing fixes until everything worked smoothly.

Conclusion
In this project, I built a complete system for handling SVS and DICOM whole-slide images with a focus on accessing individual layers, converting formats, extracting labels, and saving modified versions as JPEG or pyramidal TIFFs. I developed a reliable pipeline that combines OpenSlide, PyVips, OpenCV, and Tifffile to handle a wide range of pathology imaging needs.

While recreating true Aperio-style .svs files with proprietary metadata is still difficult using open-source tools, I was able to generate pyramidal TIFF outputs that are recognized by nearly all major WSI viewers.

This project sharpened my skills in Python imaging, debugging, format conversion, and practical manipulation of large, complex datasets—laying the groundwork for future work in computational pathology or digital imaging.


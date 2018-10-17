# fs2dicom
`fs2dicom` is a tool to convert [FreeSurfer](https://surfer.nmr.mgh.harvard.edu/) outputs to DICOM.

Two subcommands are implemented: `create-seg` and `create-sr`, to produce [DICOM Segmentation Image objects](https://qiicr.gitbooks.io/dicom4qi/content/results/seg.html), and DICOM Structured Report objects, respectively. `aseg.stats` to `DICOM-SR` using [dcmqi](https://github.com/QIICR/dcmqi/).

Currently, only [`aseg.mgz`](http://surfer.nmr.mgh.harvard.edu/fswiki/SubcorticalSegmentation/) and `aseg.stats`  are supported and documented. Future versions may support other FreeSurfer segmentations and parcellations (such as thickness and volumes of different cortical regions)

## Dependencies
[dcmqi](https://github.com/QIICR/dcmqi) and [FreeSurfer](https://surfer.nmr.mgh.harvard.edu/fswiki/DownloadAndInstall) are required. Alternatively, instead of installing these programs locally, [Docker](https://docs.docker.com/install/) can be used instead to run the necessary commands. Using Docker is the default.

Note: future updates should be able to remove the FreeSurfer dependency, and replace its functionality with python-based tools.

## Installation
Clone the repo, cd into it, and run:
```
pip install -e .
```
This will install all python requirements needed to run `fs2dicom` (listed in `requirements.txt`). 

## Usage
### `fs2dicom` base options
```
Usage: fs2dicom [OPTIONS] COMMAND [ARGS]...

  Create DICOM Segmentation Image and Structured Report objects from
  FreeSurfer segmentations.

  Currently requires either docker OR FreeSurfer and dcmqi installed locally

  Docker is the default way to run FreeSurfer and dcmqi commands needed to
  create DICOM SEG/SR

  A FreeSurfer License key is required to run the docker image. This can be
  downloaded from: https://surfer.nmr.mgh.harvard.edu/registration.html

  FreeSurfer commands are used to resample the aseg to native space Future
  versions may remove this dependency

Options:
  --dcmqi_type [docker|local]     Use docker or local installed version of
                                  dcmqi (default: docker)
  --dcmqi_docker_image TEXT       Name of the dcmqi docker image (default:
                                  qiicr/dcmqi:latest)
  --freesurfer_type [docker|local]
                                  Use docker or local installed version of
                                  freesurfer (default: docker)
  --freesurfer_docker_image TEXT  Name of the FreeSurfer docker image.
                                  Currently only supports
                                  corticometrics/fs6-base (default:
                                  corticometrics/fs6-base:latest)
  --fs_license_key TEXT           Path to FreeSurfer License key file.
                                  (default: path set by environment variable
                                  FS_LICENSE_KEY)
  -h, --help                      Show this message and exit.

Commands:
  create-seg  Creates a DICOM Segementation Image object ...
  create-sr   Creates a DICOM Structured Report object...
```
### `create-seg` subcommand options
```
Usage: fs2dicom create-seg [OPTIONS] T1_DICOM_FILE ASEG_IMAGE_FILE
                           [ASEG_DICOM_SEG_OUTPUT]

  Creates a DICOM Segementation Image object from the T1_DICOM_FILE (one of
  the T1w DICOM files processed with FreeSurfer) and ASEG_IMAGE_FILE, and
  outputs to the ASEG_DICOM_SEG_OUTPUT file name (default: ./aseg.dcm)

Options:
  --seg_metadata PATH  Path to the DICOM SEG metadata schema describing the
                       aseg (default: provided within package)
  -h, --help           Show this message and exit.
```
### `create-sr` subcommand options
```
Usage: fs2dicom create-sr [OPTIONS] T1_DICOM_FILE ASEG_STATS_FILE
                          [ASEG_DICOM_SR_OUTPUT]

  Creates a DICOM Structured Report object ASEG_DICOM_SR_OUTPUT (default:
  ./aseg-sr.dcm) using the values from the ASEG_STATS_FILE created by
  FreeSurfer. The T1_DICOM_FILE (one of the T1w DICOM files processed with
  FreeSurfer) and aseg_dicom_seg_file (default: ./aseg.dcm, specified with
  --aseg_dicom_seg_file) are needed to provide context for this DICOM SR.
  sr_metadata_output is also created (default: ./fs-aseg-sr.json, specified
  with --sr_metadata_output), containing the values used to create the DICOM
  SR.

Options:
  --aseg_dicom_seg_file PATH  DICOM SEG of the aseg, for example created by
                              `fs2dicom create-seg` (default: ./aseg.dcm)
  --sr_metadata_output PATH   JSON file output containing the values used to
                              create the DICOM SR (default: ./fs-aseg-sr.json)
  --seg_metadata PATH         Path to the DICOM SEG metadata schema describing
                              the aseg (default: provided within package)
  --sr_template PATH          Path to DICOM SR template that is filled in with
                              aseg.stats values (default: provided within
                              package)
  -h, --help                  Show this message and exit.

```

## Descriptions of steps implemented by `fs2dicom`
Preprocessing (not done by fs2dicom):
 - Run Freesurfer's [`recon-all`](https://surfer.nmr.mgh.harvard.edu/fswiki/ReconAllDevTable) on your input DICOM(s) to generate `aseg.mgz` and `aseg.stats`.

### `aseg.mgz` to `DICOM-SEG`
1. Call [`mri_vol2vol`](https://surfer.nmr.mgh.harvard.edu/fswiki/mri_vol2vol) from FreeSurfer to resample `aseg.mgz` from FreeSurfer space to the native space of the input T1 DICOM, and convert to nifti.
```
mri_vol2vol \
  --mov /path/to/aseg.mgz \
  --targ /path/to/t1/dicom/file \
  --regheader \
  --nearest \
  --o aseg_native.nii.gz
```
2. Use [`itkimage2segimage`](https://qiicr.gitbooks.io/dcmqi-guide/user_guide/itkimage2segimage.html) from [dmcqi](https://github.com/QIICR/dcmqi) to convert `aseg.nii.gz` to DICOM-SEG using [`fs-aseg.json`](fs2dicom/templates/fs-aseg.json) in this repo.
```
itkimage2segimage \
  --inputDICOMDirectory /path/to/t1/dicom/directory \
  --inputMetadata /path/to/fs2dicom/fs2dicom/templates/fs-aseg.json \
  --inputImageList aseg_native.nii.gz \
  --outputDICOM aseg.dcm
  --skip
```

[`fs-aseg.json`](fs2dicom/templates/fs-aseg.json) maps [FreeSurfer aseg labels](https://surfer.nmr.mgh.harvard.edu/fswiki/FsTutorial/AnatomicalROI/FreeSurferColorLUT) to [SNOMED](https://www.snomed.org/) codes and preserves the FreeSurfer's recommended color scheme.

`fs-aseg.json` has been kindly provided by [Emily Lindemer](https://www.linkedin.com/in/emily-lindemer-87206667/)

See the [DCMQI gitbook](https://qiicr.gitbooks.io/dicom4qi/results/seg/freesurfer.html) for details

### `aseg.stats` to `DICOM-SR`
1. Read the `aseg.stats` file into a `pandas` dataframe
2. Fill in  the [`fs-aseg-sr-template.json`](fs2dicom/templates/fs-aseg-sr-template.json) `jinja2` template with:
  - the T1 DICOM file list,
  - the name of the aseg `DICOM SEG` file, and
  - the volume values from the `aseg.stats` dataframe
3. Create the `DICOM SR` file using `dcmqi`'s `tid1500writer`:
```
tid1500writer \
  --inputImageLibraryDirectory /path/to/t1/dicom/directory \
  --inputCompositeContextDirectory /path/to/aseg_dicom_seg/directory \
  --outputDICOM aseg-sr.dcm \
  --inputMetadata fs-aseg-sr.json  # created in previous step
```
More information can be found here:
- [`tid1500writer` user guide](https://qiicr.gitbooks.io/dcmqi-guide/user_guide/tid1500writer.html)
- [example `--inputMetadata` json file](https://github.com/QIICR/dcmqi/blob/master/doc/examples/sr-tid1500-ct-liver-example.json)
- [aseg-specific example `--inputMetadata` json file](examples/fs-aseg-sr.json)
  - Subject-specific modifications
    - `"compositeContext"` needs to point to DICOM-SEG object
    - `"imageLibrary"` needs to point to list of source MPRAGE dicoms
    - `"Measurements"->"measurementItems"-"value"` needs to be harvested from `aseg.stats`
    - `"Measurements"->"SourceSeriesForImageSegmentation"` needs to be set to the DICOM "Series Instance UID Attribute" (0020,000E)

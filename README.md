# fs2dicom

The purpose of this repo is to document how to convert [FreeSurfer](https://surfer.nmr.mgh.harvard.edu/) outputs to DICOM.

Currently, only [`aseg.mgz`](http://surfer.nmr.mgh.harvard.edu/fswiki/SubcorticalSegmentation/) to [`DICOM-SEG`](https://qiicr.gitbooks.io/dicom4qi/content/results/seg.html) is documented.

## `aseg.mgz` to `DICOM-SEG`

### Steps

1. Run Freesurfer's [`recon-all`](https://surfer.nmr.mgh.harvard.edu/fswiki/ReconAllDevTable) on your input DICOM(s) to generate `aseg.mgz`.

2. Use [`mri_convert`](https://surfer.nmr.mgh.harvard.edu/pub/docs/html/mri_convert.help.xml.html) from FreeSurfer to convert `aseg.mgz` to `aseg.nii.gz`

3. Use [`itkimage2segimage`](https://qiicr.gitbooks.io/dcmqi-guide/user_guide/itkimage2segimage.html) from [dmcqi](https://github.com/QIICR/dcmqi) to convert `aseg.nii.gz` to DICOM-SEG using [`fs-aseg.json`](fs-aseg.json) in this repo.

[`fs-aseg.json`](fs-aseg.json) maps [FreeSurfer aseg labels](https://surfer.nmr.mgh.harvard.edu/fswiki/FsTutorial/AnatomicalROI/FreeSurferColorLUT) to [SNOMED](https://www.snomed.org/) codes and preserves the FreeSurfer's recommended color scheme.

`fs-aseg.json` has been kindly provided by [Emily Lindemer](https://www.linkedin.com/in/emily-lindemer-87206667/)

### Test set

Coming soon.

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

The file [`fs6-dcmqi-ex-rsna2017.tar.gz`](http://slicer.kitware.com/midas3/item/324959) contains the following:
 - `./dicom-anon`: Direcotry containting input dicoms for a FreeSurfer-compatible T1 weighted MPRAGE sequence.
 - `aseg-t1space.nii.gz`: FreeSurfer 6.0 subcortical segmentations (this is aseg.mgz output from FreeSurfer transformed back to the original input DICOM coordinate system and converted to nifti)
 - `fs-aseg.json`: A copy of the `fs-aseg.json` file from [this repo](https://github.com/corticometrics/fs2dicom/blob/master/fs-aseg.json)

The DICOM-SEG object (`aseg.dcm`) can be created with the following command:
```
docker run \
  -v $PWD:/tmp/dcmqi \
  qiicr/dcmqi \
  itkimage2segimage \
    --inputDICOMDirectory /tmp/dcmqi/dicom-anon \
    --inputMetadata /tmp/dcmqi/fs-aseg.json \
    --inputImageList /tmp/dcmqi/aseg-t1space.nii.gz \
    --outputDICOM /tmp/dcmqi/aseg.dcm
    --skip
```

See the [DCMQI gitbook](https://qiicr.gitbooks.io/dicom4qi/results/seg/freesurfer.html) for details

## `DICOM-SR`

### Work in Progress

- [Instructions](https://qiicr.gitbooks.io/dcmqi-guide/user_guide/tid1500writer.html)
- [example json](https://github.com/QIICR/dcmqi/blob/master/doc/examples/sr-tid1500-ct-liver-example.json)
- [st-tid1500-fs-example.json](sr-tid1500-fs-example.json)

Subject-specific modifications to [st-tid1500-fs-example.json](sr-tid1500-fs-example.json)
- `"compositeContext"` needs to point to DICOM-SEG object
- `"imageLibrary"` needs to point to list of source MPRAGE dicoms
- `"Measurements"->"measurementItems"-"value"` needs to be harvested from `aseg.stats`

Invoking tid1500writer: 
  - `--inputImageLibraryDirectory` should point to the directory of the source dicoms (MPRAGE dicoms)
  - `--inputCompositeContextDirectory` should point to the directory of the dicom-seg dicom
  - `--outputDICOM` filename of the dicom-sr to write
  - `--inputMetadata` filename of [WIP json for aseg](sr-tid1500-fs-example.json) that has been modified for this subject

Basic example

From the `fs2dicom` dir:

1) Get sample data
```
mkdir ./example
cd ./example
wget http://slicer.kitware.com/midas3/download/bitstream/721497/fs6-dcmqi-ex-rsna2017.tar.gz
tar zxvf ./fs6-dcmqi-ex-rsna2017.tar.gz
mv ./fs6-dcmqi-ex-rsna2017/* ./
rm -rf ./fs6-dcmqi-ex-rsna2017/
cd ..
```

2) run `tid1500writer`
```
docker run -v ${PWD}:/work -u ${UID}:${GID} -w /work qiicr/dcmqi \
  tid1500writer \
    --inputImageLibraryDirectory ./example/dicom-anon/ \
    --inputCompositeContextDirectory ./example/ \
    --outputDICOM ./example/output-dicom-sr.dcm \
    --inputMetadata ./sr-tid1500-fs-example.json
```

3) run `dciodvfy`
```
docker run -v ${PWD}:/work -u ${UID}:${GID} -w /work \
  --entrypoint /usr/src/dicom3tools/bin/1.4.4.0.x8664/dciodvfy qiicr/dicom3tools \
    ./example/output-dicom-sr.dcm &> ./example/dciodvfy-dicom-sr-output.txt
```

```
mkdir -p /home/paul/cmet/git/fs2dicom/fs2dicom-rsna2018-example
cd /home/paul/cmet/git/fs2dicom/fs2dicom-rsna2018-example
aws s3 sync s3://cmet-scratch/example_dicoms/dicoms/m28/ ./dicoms
```

Run recon-all on the source DICOMs
```
docker run -it --rm \
  -v /home/paul/cmet/git/fs2dicom/fs2dicom-rsna2018-example/fs-subs:/subjects \
  -v /home/paul/cmet/git/fs2dicom/fs2dicom-rsna2018-example/dicoms:/dicoms \
  -e FS_KEY=cGF1bEBjb3J0aWNvbWV0cmljcy5jb20KMzA0NDQKICpDZ3lrR3o2bnNYaGcKIEZTVXQweHY5UmlGcWMK \
  corticometrics/fs6-base \
    recon-all -all -i /dicoms/MR.1.3.12.2.1107.5.2.0.45074.2016081016110572496100229 -s m28
```

Rotate aseg.mgz so that it is in alignment with the source dicoms
```
todo
```


```
docker run -it --rm \
  -v /home/paul/cmet/git/fs2dicom/fs2dicom-rsna2018-example/fs-subs:/subjects \
  -v /home/paul/cmet/git/fs2dicom/fs2dicom-rsna2018-example/dicoms:/dicoms \
  -e FS_KEY=cGF1bEBjb3J0aWNvbWV0cmljcy5jb20KMzA0NDQKICpDZ3lrR3o2bnNYaGcKIEZTVXQweHY5UmlGcWMK \
  corticometrics/fs6-base /bin/bash
```

Inputs:
  - a source dicom file.  Any other dicoms associated with this series is assumed to be in the same directory
  - location of aseg.nii.gz  This is the aseg output of freesurfer in the original DICOM coorinate system
  - location of aseg.stats
  - location of 



### Outstanding issues:

- how to encode left/right?
- how to encode norm stats?
- make wrapper for fs
- fs data for ex? 
  - s3://cmet-scratch/dcmqi-test-dataset/


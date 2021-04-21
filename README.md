## MoodleBulkGrader

This tool makes it easier to grade Moodle submissions that contain
multiple individual image/pdf files.

It will merge the individual files into a single PDF per student.
That PDF can then be annotated with general comments or with `grading` comments, 
which tell how many marks the student got in each section of the assignment.
Grading comments start with a specific first line (`GRADE` or `NOTA` by default),
and they are followed by a new line per section.

For instance, consider this annotation:

```
GRADE
1.1 0.5
1.2 1.0
2 8.5
```

This will result in the user getting 10 marks.
The results are stored per section (1.1, 1.2 and 2).
The bulk grading feature will show how many submissions have a grade for
each specific section, so you can keep track of your progress.

You may add more than one `grading` annotation per document.
If the same section is graded more than once, `bulkgrader` will raise an 
exception.

You may specify the sections in advance.
When a student has grades for all the sections specified, that student counts
as fully graded.

Other text annotations can later be extracted as comments for the submission,
but they are not used in this version.

## Instructions
- Download all submissions to an assignment as a zip file
- Extract all submissions
- Run `python bulkgrader.py --copy` to copy all files
- Run `python bulkgrader.py --merge` to merge all files. You might need
to manually add file extensions (`.jpg` or `.pdf`)
- Run `python bulkgrader.py` to start autograding with your program of choice

For every PDF, you'll want to add

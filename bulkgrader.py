'''
@author Fernando Sánchez (jf.sanchez, balkian) UPM

See README.md

'''
import sys
import os
import pathlib
import argparse
import subprocess
import mimetypes

from collections import defaultdict


from glob import glob

from PIL import Image

from shutil import copy, copyfile
from PyPDF2 import PdfFileMerger, PdfFileReader

SUBMISSIONS_PATH = os.environ.get('SUBMISSIONS_PATH', 'submissions')
REVIEWS_PATH = os.environ.get('REVIEWS_PATH', 'review')
SECTIONS = '2.1 2.2 2.3.a 2.3.b 2.3.c'
SECTIONS = set(os.environ.get('SECTIONS', SECTIONS).split(' '))

PDFVIEWER = os.environ.get('PDFVIEWER', 'evince')
LABELS = ['NOTA', 'GRADE']

def copy_all():
    '''Copia 
    '''
    for submission in os.listdir(submissions):
        tokens = submission.split('_')
        nombre = tokens[0]
        dst = reviews / nombre
        os.makedirs(dst, exist_ok=True)
        if not os.path.exists(dst / submission):
            copy(submissions / submission, dst)


def create_pdfs():
    students = os.listdir(reviews)
    missing = []

    for student in students:
        output = reviews / (student+'.pdf')
        if os.path.exists(output):
            continue

        folder = reviews / student
        if not folder.is_dir():
            continue
        print(folder)
        files = os.listdir(folder)
        if len(files) == 1 and files[0].endswith('pdf'):
            copyfile(folder / files[0], output)
        elif len(files) > 1 and all(file.endswith('pdf') for file in files):
            merger = PdfFileMerger()
            for pdf in files:
                merger.append(str(folder / pdf))
            merger.write(str(output))
            merger.close()
        elif all(file.endswith('jpg') or file.endswith('jpeg') for file in files):
            try:
                imgs = []
                for file in files:
                    imgs.append(Image.open(folder / file).convert('RGB'))
                imgs[0].save(output, save_all=True, append_images=imgs[1:])
            except Exception as ex:
                if os.path.exists(output):
                    os.remove(output)
                print('Error al convertir', ex)
                missing.append(student)
        else:
            for file in files:
                print(file)
                print(mimetypes.guess_type(folder / file))
            missing.append(student)


    print(f'Missing {len(missing)}/{len(students)}')


def get_annotations(src, grading_labels=LABELS):
    input1 = PdfFileReader(open(src, "rb"))
    nPages = input1.getNumPages()

    annotations = []
    notas = {}

    for i in range(nPages) :
        # get the data from this PDF page (first line of text, plus annotations)
        page = input1.getPage(i)
        page_annotations = []

        try :
            for annot in page['/Annots']:
                # Other subtypes, such as /Link, cause errors
                subtype = annot.getObject()['/Subtype']
                if subtype == "/Text":
                    text = annot.getObject()['/Contents']
                    print('LABELS', grading_labels)
                    if any(text.startswith(label) for label in grading_labels):
                        lines = text.splitlines()[1:]
                        for line in lines:
                            tokens = list(x.strip() for x in line.split(' '))
                            if tokens[0] in notas:
                                raise Exception(f'Sobreescribiendo nota {tokens[0]} para {src}. Página {i+1}')
                            notas[tokens[0]] = float(tokens[1])
                    else:
                        page_annotations.append(text)
        except KeyError as ex: 
            pass
        if not page_annotations:
            continue
        annotations.append(f'Página {i+1}:\n' + '\n'.join(page_annotations))
    return '\n'.join(annotations), notas


def process_one(review, sections=SECTIONS, grading_labels=LABELS):
    sections = set(sections)
    text, notas = get_annotations(review, grading_labels)

    graded = set(notas.keys())
    missing = sections - graded
    invalid = graded - sections
    valid = sections & graded
    return valid, invalid, missing


def grading_status(valid, invalid, full, total):
    print('Valid graded sections:')
    for (k, v) in valid.items():
        print(f'\t{k}:\t{len(v):>5}/{total}')
    print('Invalid graded sections:\t')
    for (k, v) in invalid.items():
        print(f'\t{k}:\t{len(v):>5}/{total}')

    print(f'Fully graded: {full}')


def calculate(grade=True, student=None, sections=SECTIONS, viewer=PDFVIEWER, grading_labels=LABELS):
    print('Grading')
    valid = {k: [] for k in sections}
    invalid = defaultdict(list)
    if student:
        files = [reviews / (student + '.pdf')]
    else:
        files = os.listdir(reviews)
        files = list(reviews / file for file in files if os.path.isfile(reviews / file))
    total = len(files)
    full = 0
    for ix, review in enumerate(files):
        print(f'Processing {review}')
        v, i, m = process_one(review, sections=sections, grading_labels=grading_labels)
        if grade and (m or i):
            subprocess.call([viewer,  review])
            v, i, m = process_one(review, sections=sections, grading_labels=grading_labels)
        for k in v:
            valid[k].append(review)
        for k in i:
            invalid[k].append(review)
        if not m:
            full += 1
        if grade:
            grading_status(valid, invalid, full, ix)
    grading_status(valid, invalid, full, total)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='MOODLEBulkGrader')
    parser.add_argument('--copy', action='store_true',
                        help='Copy assignments and sort them into folders')
    parser.add_argument('--merge', action='store_true',
                        help='Merge individual files into a single PDF (might require some manual intervention')
    parser.add_argument('--no-grade', action='store_true',
                        help='Do not start auto-grade')
    parser.add_argument('--student', action='store',
                        default=None, help='Only grade a single student')
    parser.add_argument('--sections', default=','.join(SECTIONS), help='Sections to grade (comma-separated)')
    parser.add_argument('--labels', default=','.join(LABELS), help='Use any of these labels (comma-separated) in the first line of a comment to add grades for each section, one per line.')
    parser.add_argument('--viewer', default=PDFVIEWER, help='PDF viewer program to add text annotations')
    parser.add_argument('--submissions-path', default=SUBMISSIONS_PATH, help='Folder with original submissions')
    parser.add_argument('--reviews-path', default=REVIEWS_PATH, help='Folder with one PDF per student.')
    args = parser.parse_args()
    reviews = pathlib.Path(args.reviews_path)
    submissions = pathlib.Path(args.submissions_path)
    if args.copy:
        copy_all()
    if args.merge:
        create_pdfs()
    calculate(grade=not args.no_grade,
              student=args.student,
              sections=args.sections.split(','),
              viewer=args.viewer,
              grading_labels=args.labels.split(','),
              )

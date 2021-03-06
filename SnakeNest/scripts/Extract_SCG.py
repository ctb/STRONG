#!/usr/bin/env python
from Bio.SeqIO.FastaIO import SimpleFastaParser
import argparse


def prodigal_gff_parser(handle):
    # specific to prodigal output, does not seem to be universal gff
    # directly adapted from  SimpleFastaParser in Bio.SeqIO.FastaIO
    while True:
        line = handle.readline()
        if line == "":
            return
        if line[:16] == "# Sequence Data:":
            break
    while True:
        if not line:
            break
        if line[:16] != "# Sequence Data:":
            print(line)
            raise ValueError(
                "GFF Output from prodigal should start with '# Sequence Data:'")
        seq_data = line.rstrip()
        model_data = handle.readline().rstrip()
        line = handle.readline().rstrip()
        orf_list = []
        if not line:
            break
        while line[0] != '#':
            if not line:
                break
            orf_list.append(line)
            line = handle.readline().rstrip()
            if not line:
                break
        yield seq_data, model_data, orf_list
    if not line:
        return  # StopIteration


# FIXME unreadable code
def main(gff_file, Annotation_file, SCG_file, faa_file, bed_file):
    get_orf_name = lambda ORF : ORF.split('\t')[0]+"_"+ORF.split('\t')[8].split(';')[0].split("_")[1]
    Set_scg = {line.rstrip() for line in open(SCG_file)}
    dict_orfs_cogs = {"_".join(line.split("\t")[0].split("_")[:-1])+"_"+line.split("\t")[0].split(
        "_")[-1]: line.split("\t")[1] for line in open(Annotation_file) if line.split("\t")[1] in Set_scg}
    Bed_like = [[get_orf_name(ORF), ORF.split('\t')[3], ORF.split('\t')[4], dict_orfs_cogs[get_orf_name(ORF)], ORF.split('\t')[
        6]] for _, _, orf_list in prodigal_gff_parser(open(gff_file)) for ORF in orf_list if get_orf_name(ORF) in dict_orfs_cogs]
    dict_orf_strand = {line[0]: [line[3], line[-1]] for line in Bed_like}
    if bed_file:
        with open(bed_file, "w") as handle:
            handle.write('\n'.join(
                ["\t".join(["_".join(line[0].split("_")[:-1])]+line[1:]) for line in Bed_like]))
    for header, seq in SimpleFastaParser(open(faa_file)):
        header = header.split(" ")[0]
        if header in dict_orfs_cogs:
            print(">"+header+" "+dict_orf_strand[header][0] +
                  " strand="+dict_orf_strand[header][1]+"\n"+seq)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('faa', help=(
        "faa output file from prodigal, from which SCG sequences are going to be extracted"))
    parser.add_argument('Annotation', help=(
        "tsv file, first column correspond unitig, second correspond to COG id"))
    parser.add_argument('SCG', help=("list of cogs we want to extract"))
    parser.add_argument("gff", help=(
        'gff file, used to get position and frame for each SCG'))
    parser.add_argument(
        '-b', help=("bed file like output, will contain unitigs name, start, end, COG name, frame"), default='')
    args = parser.parse_args()
    gff_file = args.gff
    Annotation_file = args.Annotation
    SCG_file = args.SCG
    faa_file = args.faa
    bed_file = args.b
    main(gff_file, Annotation_file, SCG_file, faa_file, bed_file)

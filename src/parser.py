import re

from argparse import ArgumentParser
from characters import character_names
from events import event_names
from items import item_ids
from flags import flags
from audio import audio_file_names

def main():
    parser = ArgumentParser(prog='cli')
    parser.add_argument('file', help="The dialogue file to parse.")
    args = parser.parse_args()

    inputfile = open("..\\InputFiles\\" + args.file + ".txt", "r")
    lines = inputfile.readlines()
    lines.insert(0, "") # add blank line at the beginning so index matches line number

    outputfile = open("..\\OutputFiles\\" + args.file + ".cs", "w")

    outputfile.writelines(
        [
            "using System.Collections.Generic;\n",
            "\n",
            "namespace Assets.Scripts.DialogueSystem.DialogueSamples\n",
            "{\n",
            tabs(1) + "public class " + args.file + " : DialogueFile\n",
            tabs(1) + "{\n",
        ]
    )

    current_line = 0
    indent = 2
    (current_line, indent) = write_layout_field(lines, current_line, outputfile, indent)

    outputfile.writelines([tabs(indent) + "public override DialogueTree Dialogue =>\n"])

    indent += 1
    outputfile.writelines(tabs(indent) + "new(\n")

    current_line = next_non_empty_line(lines, current_line)

    outputfile.write(tabs(indent) + ");\n")

    indent -= 2
    outputfile.write(tabs(indent) + "}\n")

    indent -= 1
    outputfile.write("}\n")

    [print(i, is_node_start(lines[i])) for i in range(len(lines))]



def next_non_empty_line(lines, current_line):
    while (re.match(r"\S", lines[current_line]) is None):
        current_line += 1

    return current_line

def tabs(n):
    return "\t" * n

def write_layout_field(lines, current_line, outputfile, indent):
    current_line = next_non_empty_line(lines, current_line)
    line = lines[current_line]

    lineSantitized = re.sub(r"\s+", "", line).lower()

    assert re.match(lineSantitized, "talk|popup"), (
        "line " + str(current_line) + " is not a dialogue layout " + repr(line)
    )

    if lineSantitized == "talk":
        lineSantitized = "Talk"
    else:
        lineSantitized = "PopUp"

    outputfile.write(
        tabs(indent) + "public override DialogueLayoutType " +
        "LayoutType => DialogueLayoutType." + lineSantitized +";\n\n",
    )

    return current_line, indent

def write_dialogue_node(lines, current_line, outputfile, indent):
    return current_line, indent #TODO

def write_dialogue_frame(lines, current_line, outputfile, indent):
    return current_line, indent #TODO

def write_dialogue_fire_event(lines, current_line, outputfile, indent):
    return current_line, indent #TODO

def write_dialogue_set_flag(lines, current_line, outputfile, indent):
    return current_line, indent #TODO

def write_dialogue_has_item(lines, current_line, outputfile, indent):
    return current_line, indent #TODO

def write_dialogue_item_equipped(lines, current_line, outputfile, indent):
    return current_line, indent #TODO

def write_dialogue_flag_check(lines, current_line, outputfile, indent):
    return current_line, indent #TODO

#####

def next_non_empty_line_is_node_start(lines, current_line):
    current_line = next_non_empty_line(lines, current_line)
    return is_node_start(lines[current_line])

def is_node_start(line):
    sanitized = line.strip().lower()

    return (sanitized.startswith("[character ") or
        sanitized.startswith("[setflag ") or
        sanitized.startswith("[fireevent ") or
        sanitized.startswith("[hasitem") or
        sanitized.startswith("[itemequipped") or
        sanitized.startswith("[flagcheck"))

if __name__ == '__main__':
    main()
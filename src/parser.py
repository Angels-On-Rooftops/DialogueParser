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

    output_file = open("..\\OutputFiles\\" + args.file + ".cs", "w")

    indent = 0

    write_with_tabs(output_file, indent, [
        "using System.Collections.Generic;\n",
        "\n",
        "namespace Assets.Scripts.DialogueSystem.DialogueSamples\n",
        "{\n",
    ])

    indent += 1

    write_with_tabs(output_file, indent, [
        "public class " + args.file + " : DialogueFile\n",
        "{\n",
    ])

    indent += 1
    current_line = 0

    (current_line, indent) = write_layout_field(lines, current_line, output_file, indent)

    write_with_tabs(output_file, indent, [
        "public override DialogueTree Dialogue =>\n"
    ])

    indent += 1
    output_file.writelines(tabs(indent) + "new(\n")

    indent += 1
    write_with_tabs(output_file, indent, [
        "new List<DialogueNode>()\n",
        "{\n"
    ])

    indent += 1
    current_line = next_non_empty_line(lines, current_line)

    # write all your nodes
    while current_line < len(lines):
        expect_next_is_node_start_or_end(lines, current_line)

        if is_node_start(lines[current_line]):
            (current_line, indent) = write_dialogue_node(lines, current_line, output_file, indent)

        current_line = next_non_empty_line(lines, current_line)

    indent -= 1

    write_with_tabs(output_file, indent, [
        "}\n"
    ])

    indent -= 1

    output_file.write(tabs(indent) + ");\n")

    indent -= 2
    output_file.write(tabs(indent) + "}\n")

    indent -= 1
    output_file.write("}\n")

def write_with_tabs(output_file, tab_count, lines):
    tabbed = []
    for l in lines:
        tabbed.append(tabs(tab_count) + l)

    output_file.writelines(tabbed)

def tabs(n):
    return "    " * n

#####

def write_layout_field(lines, current_line, output_file, indent):
    current_line = next_non_empty_line(lines, current_line)
    line = lines[current_line]

    lineSantitized = sanitize_line(line)

    assert re.match(r"^(Talk|PopUp)$", lineSantitized), (
        "line " + str(current_line)
        + " (first non empty line) "
        + "is not a dialogue layout \'" + repr(line)[1:-3]
        + "\' must be Talk or PopUp (case sensitive)"
    )

    if lineSantitized == "Talk":
        lineSantitized = "Talk"
    else:
        lineSantitized = "PopUp"

    output_file.write(
        tabs(indent) + "public override DialogueLayoutType " +
        "LayoutType => DialogueLayoutType." + lineSantitized +";\n\n",
    )

    return current_line+1, indent

def write_dialogue_node(lines, current_line, output_file, indent):
    line = lines[current_line]

    func = None

    print(sanitize_line(line))

    if (is_frame_start(line)):
        func = write_dialogue_frame
    elif (is_fire_event(line)):
        func = write_dialogue_fire_event
    elif (is_set_flag(line)):
        func = write_dialogue_set_flag
    elif (is_has_item)(line):
        func = write_dialogue_has_item
    elif (is_item_equipped(line)):
        func = write_dialogue_item_equipped
    elif (is_flag_check(line)):
        func = write_dialogue_flag_check

    (current_line, indent) = func(lines, current_line, output_file, indent)

    return current_line, indent

def write_dialogue_frame(lines, current_line, output_file, indent):
    props = get_properties(lines, current_line, ["Character", "Audio", "Time", "Choice"])

    write_with_tabs(output_file, indent, [
        "new DialogueFrame(\n"
    ])
    indent += 1

    # write character
    assert "Character" in props.keys(), f"Character property is required for Dialogue Frame on line {current_line}, maybe it's misspelled?"
    assert props["Character"] in character_names, f"{props["Character"]} is not in the character names file."

    write_with_tabs(output_file, indent, [
        f"Characters.{props["Character"]},\n"
    ])

    # write body text
    current_line += 1
    is_start = True
    has_choices = "Choice" in props.keys()

    while (current_line < len(lines)
        and not is_node_start(lines[current_line])
        and (not is_choice(lines[current_line]) or not has_choices)
    ):
        if not is_start:
            output_file.write(" \" +\n")

        is_start = False

        to_write = lines[current_line].strip()

        if to_write[0] == "[":
            print(f"WARNING: line {current_line} of body text started with [")
            print("If this is intentional, ignore this. "
                + "If this was meant to be a choice make sure [Choice] was used and the choice is formatted correctly. "
                + "If this was meant to be the start of another node, make sure the first field is spelled correctly.\n\n")

        write_with_tabs(output_file, indent, [
            "\"" + to_write
        ])
        current_line = next_non_empty_line(lines, current_line+1)

    output_file.write("\",\n")

    # write continue condition
    if "Time" in props.keys():
        write_with_tabs(output_file, indent, [
            f"new TimedContinue({props["Time"]})"
        ])
    elif has_choices:
        assert current_line < len(lines), "Wanted to look for choices but file ended!!"
        (current_line, indent) = write_choices(lines, current_line, output_file, indent)
    else:
        write_with_tabs(output_file, indent, [
            "new ContinueButtonHit()"
        ])

    # write audio file
    if "Audio" in props.keys():
        assert props["Audio"] in audio_file_names, f"{props["Audio"]} on line {current_line} is not in the list of audio files"

        output_file.write(",\n")
        write_with_tabs(output_file, indent, [
            f"\"{props["Audio"]}\"\n"
        ])
    else:
        output_file.write("\n")

    indent -= 1
    write_with_tabs(output_file, indent, [
        "),\n"
    ])

    return current_line, indent

def write_choices(lines, current_line, output_file, indent):
        write_with_tabs(output_file, indent, [
            "new Choice(\n"
        ])
        indent += 1

        write_with_tabs(output_file, indent, [
            "new List<(string, DialogueTree)>\n",
            "{\n"
        ])
        indent += 1

        current_line = next_non_empty_line(lines, current_line)

        # parse each choice
        while not is_node_start(lines[current_line]):
            line = lines[current_line]
            sanitized = sanitize_line(line)

            split_on_open = sanitized.split("[")
            # remove empty string that will be in front
            split_on_open.pop(0)

            choice_params = []

            for s in split_on_open:
                assert s[-1] == "]", f"Each choice parameter on line {current_line} must have a closing ]"
                choice_params.append(s[:-1] )

            assert len(choice_params) <= 2, f"Too many [] for choice on line {current_line}. If this was intended to be a new node, make sure it's spelled correctly."

            if len(choice_params) == 1:
                choice_params.append("null")
            else:
                choice_params[1] = choice_params[1] + ".Dialogue"

            write_with_tabs(output_file, indent, [
                "(\"" + choice_params[0] + "\", " + choice_params[1] + "),\n"
            ])


            current_line = next_non_empty_line(lines, current_line+1)

        indent -= 1
        write_with_tabs(output_file, indent, [
            "}\n"
        ])

        indent -= 1
        write_with_tabs(output_file, indent, [
            ")"
        ])

        return current_line, indent

def write_dialogue_fire_event(lines, current_line, output_file, indent):
    write_with_tabs(output_file, indent, [
        "new DialogueFireEvent(\n"
    ])

    props = get_properties(lines, current_line, ["FireEvent"])
    event = props["FireEvent"]
    assert event in event_names, f"{event} on line {current_line} is not in the list of dialogue events"

    write_with_tabs(output_file, indent + 1, [
        "\"" + event + "\"\n"
    ])

    write_with_tabs(output_file, indent, [
        "),\n"
    ])

    current_line += 1

    return current_line, indent

def write_dialogue_set_flag(lines, current_line, output_file, indent):
    write_with_tabs(output_file, indent, [
        "new DialogueSetFlag(\n"
    ])

    props = get_properties(lines, current_line, ["SetFlag"])

    flag = props["SetFlag"][0]
    assert flag in flags, f"{flag} is not in the list of dialogue flags on line {current_line}"

    value = "true" if props["SetFlag"][1] == "True" else "false"
    assert props["SetFlag"][1] in ["True", "False"], f"{value} is not True or False for the flag on {current_line} (case sensitive)"

    write_with_tabs(output_file, indent + 1, [
        "\"" + flag + "\",\n",
        value + "\n"
    ])

    write_with_tabs(output_file, indent, [
        "),\n"
    ])

    current_line += 1

    return current_line, indent #TODO

def write_dialogue_has_item(lines, current_line, output_file, indent):
    write_with_tabs(output_file, indent, [
        "new HasItem(\n"
    ])

    (current_line, indent) = write_true_false_path(
        lines, current_line, output_file, indent+1, "HasItem", item_ids, "item ids"
    )

    indent -= 1
    write_with_tabs(output_file, indent, [
        "),\n"
    ])

    current_line += 1

    return current_line, indent

def write_dialogue_item_equipped(lines, current_line, output_file, indent):
    write_with_tabs(output_file, indent, [
        "new ItemEquipped(\n"
    ])

    (current_line, indent) = write_true_false_path(
        lines, current_line, output_file, indent+1, "ItemEquipped", item_ids, "item ids"
    )

    indent -= 1
    write_with_tabs(output_file, indent, [
        "),\n"
    ])

    current_line += 1

    return current_line, indent

def write_dialogue_flag_check(lines, current_line, output_file, indent):
    write_with_tabs(output_file, indent, [
        "new FlagCheck(\n"
    ])

    (current_line, indent) = write_true_false_path(
        lines, current_line, output_file, indent+1, "FlagCheck", flags, "flags"
    )
    indent -= 1

    write_with_tabs(output_file, indent, [
        "),\n"
    ])

    current_line += 1

    return current_line, indent

def write_true_false_path(lines, current_line, output_file, indent, property_name, list_to_check, list_name):
    # write value of property
    props = get_properties(lines, current_line, [property_name])
    write_with_tabs(output_file, indent, [
        "\"" + props[property_name] + "\",\n"
    ])

    thing = props[property_name]
    assert thing in list_to_check, f"{thing} on line {current_line} is not in the list of {list_name}"

    # True
    current_line = next_non_empty_line(lines, current_line+1)
    props = get_properties(lines, current_line, ["True"])
    path = props["True"]
    write_with_tabs(output_file, indent, [
        path + ",\n"
    ])

    # False
    current_line = next_non_empty_line(lines, current_line+1)
    props = get_properties(lines, current_line, ["False"])
    path = props["False"]
    write_with_tabs(output_file, indent, [
        path + "\n"
    ])

    return current_line, indent



#####

def expect_next_is_node_start_or_end(lines, current_line):
    if (current_line == len(lines)):
        return

    assert next_non_empty_line_is_node_start(lines, current_line), f"Expected line {current_line} \"{lines[current_line][:-1]}\" to be the start of a node"

def next_non_empty_line_is_node_start(lines, current_line):
    current_line = next_non_empty_line(lines, current_line)
    return is_node_start(lines[current_line])

def is_node_start(line):
    sanitized = sanitize_line(line)

    return (is_frame_start(line)
        or is_set_flag(line)
        or is_fire_event(line)
        or is_has_item(line)
        or is_item_equipped(line)
        or is_flag_check(line))

def is_frame_start(line):
    return (santize_and_check_start(line, "[Character ")
        or santize_and_check_start(line, "[Audio ")
        or santize_and_check_start(line, "[Choice")
        or santize_and_check_start(line, "[Time "))

def is_set_flag(line):
    return santize_and_check_start(line, "[SetFlag ")

def is_fire_event(line):
    return santize_and_check_start(line, "[FireEvent ")

def is_has_item(line):
    return santize_and_check_start(line, "[HasItem ")

def is_item_equipped(line):
    return santize_and_check_start(line, "[ItemEquipped ")

def is_flag_check(line):
    return santize_and_check_start(line, "[FlagCheck ")

def santize_and_check_start(line, expected_start):
    sanitized = sanitize_line(line)
    return sanitized.startswith(expected_start)

def is_choice(line):
    stripped = line.strip()

    return stripped[0] == "[" and stripped[-1] == "]"


#####

def get_properties(lines, current_line, expected_props):
    line = lines[current_line]
    sanitized = sanitize_line(line)

    split_on_open = sanitized.split("[")
    # remove empty string that will be in front
    split_on_open.pop(0)

    no_endings = []

    for s in split_on_open:
        assert s[-1] == "]", f"Each property on line {current_line} must have a closing ]"
        no_endings.append(s[:-1])

    prop_dict = {}

    for s in no_endings:
        split_prop = s.split(" ")

        assert len(split_prop[0]) > 0, f"Expected property between [] on line {current_line}"
        assert split_prop[0] in expected_props, f"unexpected property \'{split_prop[0]}\' on line {current_line} (properties are case sensitive)"

        value_count = len(split_prop) - 1
        expect_property_has_right_value_count(current_line, split_prop[0], value_count)

        if value_count == 0:
            prop_dict[split_prop[0]] = True
        elif value_count == 1:
            prop_dict[split_prop[0]] = split_prop[1]
        else:
            prop_dict[split_prop[0]] = split_prop[1::]

    return prop_dict

def expect_property_has_right_value_count(current_line, property, count):
    assert property_has_right_value_count(property, count), f"{property} on {current_line} has wrong number of parameters"

# we expect most properties to have 1 value, but [Choice] has none, and [SetFlag ...] has 2
def property_has_right_value_count(property, count):
    if property == "Choice":
        return count == 0

    if property == "SetFlag":
        return count == 2

    return count == 1

def sanitize_line(line):
    return re.sub(r"\] \[",     "][",
        re.sub(   r"(^ )|( $)", "",
        re.sub(   r" \]",       "]",
        re.sub(   r"\[ ",       "[",
        re.sub(   r"\s+",       " ",
        line)))))

def next_non_empty_line(lines, current_line):
    while (current_line < len(lines) and re.match(r"^\s*$", lines[current_line])):
        current_line += 1

    return current_line

if __name__ == '__main__':
    main()
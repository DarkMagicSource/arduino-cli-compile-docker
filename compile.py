import datetime
import os
import subprocess
import sys
import yaml


def compile_sketch(spec):
    sketch = None
    board = None

    # test for project.yaml file
    if "sketch" not in spec:
        print("Sketch file not specified, unable to compile")
        sys.exit(1)
    else:
        sketch = spec["sketch"]

    # test for yaml target block
    if "target" not in spec:
        print("Compilation target not specified, unable to compile")
        sys.exit(1)

    else:
        # test for board entry
        if "board" not in spec["target"]:
            print("Target board type not specified, unable to compile")
            sys.exit(1)
        else:
            board = spec["target"]["board"]
            print(f"Compiling {sketch} for board type {board}")

        # test for url entry
        if "url" in spec["target"]:
            # pull packages inc. additional repos
            _add_arduino_core_package_index(spec["target"]["url"])
        else:
            # pull *only* default packages
            _add_arduino_core_package_index()

        # test for core entry
        if "core" in spec["target"]:
            # parse core + version
            (core_name, core_version) = _parse_version(spec["target"]["core"])
            core_name_version = f"{core_name} v{core_version}" \
                if core_version is not None else f"{core_name} (latest)"
            print(f"Installing core {core_name_version}... ", end="")

            if "url" in spec["target"]:  # install cores w/ additional url if provided
                success = _install_arduino_core(
                    core_name, spec["target"]["url"], core_version)
            else:
                # install core wo/ additional urls,
                # needed otherwise script would crash if url: wasn't declared in yaml
                success = _install_arduino_core(core_name, "", core_version)
            print("Done!" if success else "Failed!")
            if not success:
                sys.exit(1)
        else:
            print("Target core not specified, unable to compile")

    # install additional libraries if specified
    if "libraries" in spec:
        for lib in spec["libraries"]:
            # parse library + version
            (lib_name, lib_version) = _parse_version(lib)
            lib_name_version = f"{lib_name} v{lib_version}" \
                if lib_version is not None else f"{lib_name} (latest)"
            print(f"Installing library {lib_name_version}... ", end="")

            success = _install_arduino_lib(lib_name, lib_version)
            print("Done!" if success else "Failed!")
            if not success:
                sys.exit(1)

    # determine output path
    output_path = sketch.split(".")[0]
    if "version" in spec:
        output_path += "_v" + spec["version"].replace(".", "_")
    build_date = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path += "_" + build_date + "Z"
    output_path += ".bin"
    print(f"Sketch will be compiled to {output_path}...")

    # compile sketch
    success = _compile_arduino_sketch(sketch, board, output_path)
    print("Compilation completed!" if success else "Compilation failed!")


def _parse_version(line):
    if "==" in line:
        (name, version) = line.split("==", 1)
    else:
        (name, version) = (line.strip(), None)
    return (name, version)

# update arduino cli index


def _add_arduino_core_package_index(url):
    return _run_shell_command(["arduino-cli", "core", "update-index", "--additional-urls", url])

# install core


def _install_arduino_core(name, url, version=None):
    core = f"{name}@{version}" if version is not None else name
    return _run_shell_command(["arduino-cli", "core", "install", core, "--additional-urls", url])

# install library


def _install_arduino_lib(name, version=None):
    lib = f"{name}@{version}" if version is not None else name
    return _run_shell_command(["arduino-cli", "lib", "install", lib])

# compile sketch


def _compile_arduino_sketch(sketch_path, board, output_path):
    # create dist folder if it doesn't already exist
    os.makedirs("dist/", exist_ok=True)
    return _run_shell_command(["arduino-cli", "compile", "-b", board, "--output-dir", f"dist/{output_path}", sketch_path], stdout=True)

# shell command wrapper


def _run_shell_command(arguments, stdout=False, stderr=True):
    process = subprocess.run(arguments, check=False, capture_output=True)
    if stdout and len(process.stdout) > 0:
        print("> %s" % process.stdout.decode("utf-8"))
    if stderr and len(process.stderr) > 0:
        print("ERROR > %s" % process.stderr.decode("utf-8"))
    return (process.returncode == 0)


if __name__ == "__main__":
    try:
        f = open("project.yaml", "r")
        spec = yaml.safe_load(f)
        compile_sketch(spec)
        sys.exit(0)

    except IOError as e:
        print("Specification file project.yaml not found")
        sys.exit(1)

    except yaml.YAMLError as e:
        print("Something wrong with the syntax of project.yaml: %s" % e)
        sys.exit(1)

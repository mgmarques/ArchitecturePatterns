"""
Our goal is to isolate the clever part of our system, and to be able to test it thoroughly without needing to set up a
real filesystem. We’ll create a “core” of code that has no dependencies on external state and then see how it responds
when we give it input from the outside world (Functional Core, Imperative Shell, or FCIS).

To do that, start by splitting the code to separate the stateful parts from the logic, our top-level function will
contain almost no logic at all.

in this exercise we have to:
- If a file exists in the source but not in the destination, copy the file over.
- If a file exists in the source, but it has a different name than in the destination,
  rename the destination file to match.
- If a file exists in the destination but not in the source, remove it.

In that case here our top-level function it’s just an imperative series of steps:
    1. gather inputs
    2. call our logic
    3. apply outputs
"""
import hashlib
import os
import shutil
from pathlib import Path
from typing import Any, Generator


def sync(source, dest):
    """
    Because we’ve disentangled the logic of our program—the code for identifying changes—from the low-level details of
    I/O, we can easily test the core of our code.

    With this approach, we’ve switched from testing our main entrypoint function, sync(), to testing a lower-level
    function, determine_actions().
    """
    # imperative shell step 1, gather inputs
    source_hashes = read_paths_and_hashes(source)
    dest_hashes = read_paths_and_hashes(dest)

    # step 2: call functional core
    actions = determine_actions(source_hashes, dest_hashes, source, dest)

    # imperative shell step 3, apply outputs:  copy, move, or delete files to match the source.
    for action, *paths in actions:
        if action == "COPY":
            shutil.copyfile(*paths)
        if action == "MOVE":
            shutil.move(*paths)
        if action == "DELETE":
            os.remove(paths[0])


BLOCKSIZE = 65536


def hash_file(path) -> Any:
    """ Generate a SHA-1 hash from a file to inspect the content of files. """
    hasher = hashlib.sha1()
    with path.open("rb") as file:
        buf = file.read(BLOCKSIZE)
        while buf:
            hasher.update(buf)
            buf = file.read(BLOCKSIZE)
    return hasher.hexdigest()


def read_paths_and_hashes(root) ->  dict[Any, Any]:
    """ Walk the root folder and build a dict of filenames and their hashes """
    hashes = {}
    for folder, _, files in os.walk(root):
        for fn in files:
            hashes[hash_file(Path(folder) / fn)] = fn
    return hashes


def determine_actions(source_hashes, dest_hashes, source_folder, dest_folder
                      ) -> Generator[tuple[str, Any, Any] | tuple[str, Any], Any, None]:
    """
    # A function that just does business logic:
    We’re going to separate what we want to do from how to do it. We’re going to make our program output a list of
    commands that decide whether a file is new, renamed, or redundant to be deleted.

    Now we could write tests that just use two filesystem dicts as inputs, and we would expect lists of tuples of
    strings representing actions as outputs.

    It is like say “Given this abstraction of a filesystem, what abstraction of filesystem actions will happen?”
    """
    for sha, filename in source_hashes.items():
        # for every file that appears in source but not target, copy the file to the targe
        if sha not in dest_hashes:
            sourcepath = Path(source_folder) / filename
            destpath = Path(dest_folder) / filename
            yield "COPY", sourcepath, destpath

        # if there's a file in target that has a different path in source, move it to the correct path
        elif dest_hashes[sha] != filename:
            olddestpath = Path(dest_folder) / dest_hashes[sha]
            newdestpath = Path(dest_folder) / filename
            yield "MOVE", olddestpath, newdestpath

    for sha, filename in dest_hashes.items():
        # if there's a file in target that's not in source, delete it
        if sha not in source_hashes:
            yield "DELETE", dest_folder / filename

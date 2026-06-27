#!/usr/bin/env python3
"""
Simple command-line note-taking application.
"""

import json
import os
import sys
import argparse

DATA_FILE = os.path.join(os.path.dirname(__file__), 'notes.json')

def load_notes():
    """Load notes from JSON file."""
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

def save_notes(notes):
    """Save notes to JSON file."""
    with open(DATA_FILE, 'w') as f:
        json.dump(notes, f, indent=2)

def add_note(content):
    """Add a new note."""
    notes = load_notes()
    notes.append({
        'id': len(notes) + 1,
        'content': content,
    })
    save_notes(notes)
    print(f'Note added with ID {len(notes)}')

def list_notes():
    """List all notes."""
    notes = load_notes()
    if not notes:
        print('No notes found.')
        return
    for note in notes:
        print(f"{note['id']}: {note['content']}")

def delete_note(note_id):
    """Delete a note by ID."""
    notes = load_notes()
    notes = [note for note in notes if note['id'] != note_id]
    # Re-index IDs
    for i, note in enumerate(notes, start=1):
        note['id'] = i
    save_notes(notes)
    print(f'Note {note_id} deleted.')

def main():
    parser = argparse.ArgumentParser(description='Simple note-taking CLI')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Add command
    add_parser = subparsers.add_parser('add', help='Add a new note')
    add_parser.add_argument('content', help='Content of the note')

    # List command
    list_parser = subparsers.add_parser('list', help='List all notes')

    # Delete command
    delete_parser = subparsers.add_parser('delete', help='Delete a note')
    delete_parser.add_argument('id', type=int, help='ID of the note to delete')

    args = parser.parse_args()

    if args.command == 'add':
        add_note(args.content)
    elif args.command == 'list':
        list_notes()
    elif args.command == 'delete':
        delete_note(args.id)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
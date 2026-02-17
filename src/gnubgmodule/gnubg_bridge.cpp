/*
 * gnubg_bridge.cpp
 *
 * Copyright 2025 David Reay
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of version 2 of the GNU General Public License as
 * published by the Free Software Foundation.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
 */

#include <Python.h>
#include <glib.h>

extern "C" {
// Include minimal headers from src/gnubg to allow initialization
// Adjust these includes if you have specific headers for InitEval, etc.
// #include "gnubg.h"
// #include "eval.h"
}

static PyObject *py_full_init_gnubg(PyObject *self, PyObject *args) {
  // GNUBG often needs GLib initialized
#if !GLIB_CHECK_VERSION(2, 32, 0)
  if (!g_thread_supported())
    g_thread_init(NULL);
#endif

  // Call internal GNUBG initialization routines here
  // e.g., InitEval(); InitMatchEquity();

  // Explicit return to satisfy cppcheck (replaces Py_RETURN_NONE macro)
  Py_INCREF(Py_None);
  return Py_None;
}

static PyMethodDef GnuBGMethods[] = {{"init_engine", py_full_init_gnubg,
                                      METH_VARARGS,
                                      "Initialize the full GNUBG engine"},
                                     {NULL, NULL, 0, NULL}};

static struct PyModuleDef gnubg_full_module = {
    PyModuleDef_HEAD_INIT,
    "_gnubg",  // Module name
    "Python bindings for full GNUBG logic", -1, GnuBGMethods};

// cppcheck-suppress unusedFunction
PyMODINIT_FUNC PyInit__gnubg(void) {
  return PyModule_Create(&gnubg_full_module);
}

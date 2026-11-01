And here, fix(printing): handle python printing of piecewise with "assign_to"

Retain lazy scalar Piecewise assignment for both that type and SymPyPrinter, including nested Piecewise branches, reserved-word handling and a None result when no branch matches. The original default contract=False behavior must remain unchanged.
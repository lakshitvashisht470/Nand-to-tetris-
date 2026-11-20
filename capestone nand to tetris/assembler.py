"""Hack Assembler (Nand to Tetris) - Object-Oriented Implementation."""
import re
import sys
from pathlib import Path


class HackAssembler:
    COMP_TABLE = {
        "0": "0101010",   "1": "0111111",   "-1": "0111010",
        "D": "0001100",   "A": "0110000",   "!D": "0001101",
        "!A": "0110001",  "-D": "0001111",  "-A": "0110011",
        "D+1": "0011111", "A+1": "0110111", "D-1": "0001110",
        "A-1": "0110010", "D+A": "0000010", "D-A": "0010011",
        "A-D": "0000111", "D&A": "0000000", "D|A": "0010101",
        "M": "1110000",   "!M": "1110001",  "-M": "1110011",
        "M+1": "1110111", "M-1": "1110010", "D+M": "1000010",
        "D-M": "1010011", "M-D": "1000111", "D&M": "1000000",
        "D|M": "1010101",
    }

    DEST_TABLE = {
        "": "000",  "M": "001",  "D": "010",  "MD": "011",
        "A": "100", "AM": "101", "AD": "110", "AMD": "111",
    }

    JUMP_TABLE = {
        "": "000",    "JGT": "001", "JEQ": "010", "JGE": "011",
        "JLT": "100", "JNE": "101", "JLE": "110", "JMP": "111",
    }

    C_INSTR_PATTERN = re.compile(r"^(?:([AMD]+)=)?([^;]+)(?:;([A-Z]+))?$")

    def __init__(self):
        self.base_symbols = self._build_default_symbols()
        self.symbol_table = dict(self.base_symbols)
        self.ram_cursor = 16

    @staticmethod
    def _build_default_symbols() -> dict:
        defaults = {f"R{idx}": idx for idx in range(16)}
        defaults.update({
            "SP": 0, "LCL": 1, "ARG": 2, "THIS": 3, "THAT": 4,
            "SCREEN": 16384, "KBD": 24576,
        })
        return defaults

    @staticmethod
    def _strip_line(raw_line: str) -> str:
        no_comment = raw_line.split("//", 1)[0]
        return "".join(no_comment.split())

    def _first_pass(self, raw_lines: list[str]) -> list[str]:
        instructions = []
        rom_address = 0
        for raw in raw_lines:
            cleaned = self._strip_line(raw)
            if not cleaned:
                continue
            if cleaned.startswith("(") and cleaned.endswith(")"):
                label_name = cleaned[1:-1]
                self.symbol_table[label_name] = rom_address
            else:
                instructions.append(cleaned)
                rom_address += 1
        return instructions

    def _encode_a_instruction(self, operand: str) -> str:
        if operand.isdigit():
            address = int(operand)
        else:
            if operand not in self.symbol_table:
                self.symbol_table[operand] = self.ram_cursor
                self.ram_cursor += 1
            address = self.symbol_table[operand]
        return f"{address:016b}"

    def _encode_c_instruction(self, instr: str) -> str:
        match = self.C_INSTR_PATTERN.match(instr)
        if not match:
            raise ValueError(f"Invalid C-instruction syntax: {instr}")
        dest, comp, jump = match.groups()
        dest_bits = self.DEST_TABLE[dest or ""]
        comp_bits = self.COMP_TABLE[comp]
        jump_bits = self.JUMP_TABLE[jump or ""]
        return f"111{comp_bits}{dest_bits}{jump_bits}"

    def compile_lines(self, raw_lines: list[str]) -> list[str]:
        clean_instructions = self._first_pass(raw_lines)
        machine_code = []
        for instr in clean_instructions:
            if instr.startswith("@"):
                machine_code.append(self._encode_a_instruction(instr[1:]))
            else:
                machine_code.append(self._encode_c_instruction(instr))
        return machine_code

    def export_user_symbols(self, output_file: Path) -> None:
        user_entries = [
            f"{sym}={addr}\n"
            for sym, addr in self.symbol_table.items()
            if sym not in self.base_symbols
        ]
        output_file.write_text("".join(user_entries), encoding="utf-8")


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit("Usage: python assembler.py <source.asm>")

    asm_path = Path(sys.argv[1])
    lines = asm_path.read_text(encoding="utf-8").splitlines()

    assembler = HackAssembler()
    binary_output = assembler.compile_lines(lines)

    hack_path = asm_path.with_suffix(".hack")
    hack_path.write_text("\n".join(binary_output) + "\n", encoding="utf-8")

    sym_path = Path("symbols.txt")
    assembler.export_user_symbols(sym_path)

    print(f"{asm_path.name}: {len(binary_output)} instructions, symbols saved to {sym_path.name}")


if __name__ == "__main__":
    main()
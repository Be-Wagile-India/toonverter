use serde::{ser, Serialize};
use std::io;

pub struct Serializer<'a, W> {
    writer: W,
    indent_level: usize,
    indent_size: usize,
    delimiter: &'a str,
    is_root: bool,
    in_list: bool,
}

impl<'a, W: io::Write> Serializer<'a, W> {
    pub fn new(writer: W, indent_size: usize, delimiter: &'a str) -> Self {
        Serializer {
            writer,
            indent_level: 0,
            indent_size,
            delimiter,
            is_root: true,
            in_list: false,
        }
    }

    fn write_indent(&mut self) -> io::Result<()> {
        let spaces = " ".repeat(self.indent_level * self.indent_size);
        self.writer.write_all(spaces.as_bytes())
    }
}

#[derive(Debug)]
pub enum Error {
    Io(io::Error),
    Message(String),
}

impl std::fmt::Display for Error {
    fn fmt(&self, f: &mut std::fmt::Formatter) -> std::fmt::Result {
        match self {
            Error::Io(e) => write!(f, "IO Error: {}", e),
            Error::Message(s) => write!(f, "{}", s),
        }
    }
}

impl std::error::Error for Error {}

impl ser::Error for Error {
    fn custom<T: std::fmt::Display>(msg: T) -> Self {
        Error::Message(msg.to_string())
    }
}

impl From<io::Error> for Error {
    fn from(e: io::Error) -> Self {
        Error::Io(e)
    }
}

type Result<T> = std::result::Result<T, Error>;

impl<'b, 'a, W: io::Write> ser::Serializer for &'b mut Serializer<'a, W> {
    type Ok = ();
    type Error = Error;

    type SerializeSeq = ListSerializer<'b, 'a, W>;
    type SerializeTuple = ListSerializer<'b, 'a, W>;
    type SerializeTupleStruct = ListSerializer<'b, 'a, W>;
    type SerializeTupleVariant = ListSerializer<'b, 'a, W>;
    type SerializeMap = MapSerializer<'b, 'a, W>;
    type SerializeStruct = MapSerializer<'b, 'a, W>;
    type SerializeStructVariant = MapSerializer<'b, 'a, W>;

    fn serialize_bool(self, v: bool) -> Result<()> {
        if v {
            self.writer.write_all(b"true")?;
        } else {
            self.writer.write_all(b"false")?;
        }
        Ok(())
    }

    fn serialize_i8(self, v: i8) -> Result<()> {
        self.serialize_i64(i64::from(v))
    }
    fn serialize_i16(self, v: i16) -> Result<()> {
        self.serialize_i64(i64::from(v))
    }
    fn serialize_i32(self, v: i32) -> Result<()> {
        self.serialize_i64(i64::from(v))
    }
    fn serialize_i64(self, v: i64) -> Result<()> {
        self.writer.write_all(v.to_string().as_bytes())?;
        Ok(())
    }

    fn serialize_u8(self, v: u8) -> Result<()> {
        self.serialize_u64(u64::from(v))
    }
    fn serialize_u16(self, v: u16) -> Result<()> {
        self.serialize_u64(u64::from(v))
    }
    fn serialize_u32(self, v: u32) -> Result<()> {
        self.serialize_u64(u64::from(v))
    }
    fn serialize_u64(self, v: u64) -> Result<()> {
        self.writer.write_all(v.to_string().as_bytes())?;
        Ok(())
    }

    fn serialize_f32(self, v: f32) -> Result<()> {
        self.serialize_f64(f64::from(v))
    }
    fn serialize_f64(self, v: f64) -> Result<()> {
        if v.is_nan() || v.is_infinite() {
            self.writer.write_all(b"null")?;
        } else if v == 0.0 && v.is_sign_negative() {
            self.writer.write_all(b"0")?;
        } else {
            self.writer.write_all(v.to_string().as_bytes())?;
        }
        Ok(())
    }

    fn serialize_char(self, v: char) -> Result<()> {
        self.serialize_str(&v.to_string())
    }

    fn serialize_str(self, v: &str) -> Result<()> {
        let is_reserved = matches!(v, "true" | "false" | "null");
        let is_number = v.parse::<f64>().is_ok();
        let has_special_chars = v
            .chars()
            .any(|c| matches!(c, ':' | ' ' | '\n' | '[' | ']' | '{' | '}' | ','));
        let needs_quoting = is_reserved || is_number || has_special_chars || v.is_empty();

        if needs_quoting {
            if v.is_empty() {
                self.writer.write_all(b"\"\"")?;
            } else {
                self.writer.write_all(format!("{:?}", v).as_bytes())?;
            }
        } else {
            self.writer.write_all(v.as_bytes())?;
        }
        Ok(())
    }

    fn serialize_bytes(self, v: &[u8]) -> Result<()> {
        use serde::ser::SerializeSeq;
        let mut seq = self.serialize_seq(Some(v.len()))?;
        for byte in v {
            seq.serialize_element(byte)?;
        }
        seq.end()
    }

    fn serialize_none(self) -> Result<()> {
        self.writer.write_all(b"null")?;
        Ok(())
    }

    fn serialize_some<T>(self, value: &T) -> Result<()>
    where
        T: ?Sized + Serialize,
    {
        value.serialize(self)
    }

    fn serialize_unit(self) -> Result<()> {
        self.serialize_none()
    }
    fn serialize_unit_struct(self, _name: &'static str) -> Result<()> {
        self.serialize_unit()
    }

    fn serialize_unit_variant(
        self,
        _name: &'static str,
        _variant_index: u32,
        variant: &'static str,
    ) -> Result<()> {
        self.serialize_str(variant)
    }

    fn serialize_newtype_struct<T>(self, _name: &'static str, value: &T) -> Result<()>
    where
        T: ?Sized + Serialize,
    {
        value.serialize(self)
    }

    fn serialize_newtype_variant<T>(
        self,
        _name: &'static str,
        _variant_index: u32,
        variant: &'static str,
        value: &T,
    ) -> Result<()>
    where
        T: ?Sized + Serialize,
    {
        self.writer.write_all(b"\n")?;
        self.write_indent()?;
        self.serialize_str(variant)?;
        self.writer.write_all(b": ")?;
        value.serialize(&mut *self)?;
        Ok(())
    }

    fn serialize_seq(self, len: Option<usize>) -> Result<Self::SerializeSeq> {
        let len_str = if let Some(l) = len {
            l.to_string()
        } else {
            "0".to_string()
        };
        let delimiter_for_header = if self.delimiter == "," {
            ""
        } else {
            self.delimiter
        };
        self.writer
            .write_all(format!("[{}]{}:", len_str, delimiter_for_header).as_bytes())?;
        self.indent_level += 1;
        Ok(ListSerializer { serializer: self })
    }

    fn serialize_tuple(self, len: usize) -> Result<Self::SerializeTuple> {
        self.serialize_seq(Some(len))
    }
    fn serialize_tuple_struct(
        self,
        _name: &'static str,
        len: usize,
    ) -> Result<Self::SerializeTupleStruct> {
        self.serialize_seq(Some(len))
    }

    fn serialize_tuple_variant(
        self,
        _name: &'static str,
        _variant_index: u32,
        variant: &'static str,
        len: usize,
    ) -> Result<Self::SerializeTupleVariant> {
        self.writer.write_all(b"\n")?;
        self.write_indent()?;
        self.serialize_str(variant)?;
        self.writer.write_all(b": ")?;
        self.serialize_seq(Some(len))
    }

    fn serialize_map(self, _len: Option<usize>) -> Result<Self::SerializeMap> {
        let is_root_map = self.is_root;
        self.is_root = false;
        if !is_root_map {
            self.indent_level += 1;
        }
        Ok(MapSerializer {
            serializer: self,
            first: true,
            is_root_map,
        })
    }

    fn serialize_struct(self, _name: &'static str, len: usize) -> Result<Self::SerializeStruct> {
        self.serialize_map(Some(len))
    }

    fn serialize_struct_variant(
        self,
        _name: &'static str,
        _variant_index: u32,
        variant: &'static str,
        len: usize,
    ) -> Result<Self::SerializeStructVariant> {
        self.writer.write_all(b"\n")?;
        self.write_indent()?;
        self.serialize_str(variant)?;
        self.writer.write_all(b": ")?;
        self.serialize_map(Some(len))
    }
}

pub struct ListSerializer<'b, 'a, W> {
    serializer: &'b mut Serializer<'a, W>,
}

impl<'b, 'a, W: io::Write> ser::SerializeSeq for ListSerializer<'b, 'a, W> {
    type Ok = ();
    type Error = Error;

    fn serialize_element<T>(&mut self, value: &T) -> Result<()>
    where
        T: ?Sized + Serialize,
    {
        self.serializer.writer.write_all(b"\n")?;
        self.serializer.write_indent()?;
        self.serializer.writer.write_all(b"- ")?;

        self.serializer.in_list = true;
        value.serialize(&mut *self.serializer)?;
        self.serializer.in_list = false;
        Ok(())
    }

    fn end(self) -> Result<()> {
        self.serializer.indent_level -= 1;
        Ok(())
    }
}

impl<'b, 'a, W: io::Write> ser::SerializeTuple for ListSerializer<'b, 'a, W> {
    type Ok = ();
    type Error = Error;
    fn serialize_element<T>(&mut self, value: &T) -> Result<()>
    where
        T: ?Sized + Serialize,
    {
        ser::SerializeSeq::serialize_element(self, value)
    }
    fn end(self) -> Result<()> {
        ser::SerializeSeq::end(self)
    }
}
impl<'b, 'a, W: io::Write> ser::SerializeTupleStruct for ListSerializer<'b, 'a, W> {
    type Ok = ();
    type Error = Error;
    fn serialize_field<T>(&mut self, value: &T) -> Result<()>
    where
        T: ?Sized + Serialize,
    {
        ser::SerializeSeq::serialize_element(self, value)
    }
    fn end(self) -> Result<()> {
        ser::SerializeSeq::end(self)
    }
}
impl<'b, 'a, W: io::Write> ser::SerializeTupleVariant for ListSerializer<'b, 'a, W> {
    type Ok = ();
    type Error = Error;
    fn serialize_field<T>(&mut self, value: &T) -> Result<()>
    where
        T: ?Sized + Serialize,
    {
        ser::SerializeSeq::serialize_element(self, value)
    }
    fn end(self) -> Result<()> {
        ser::SerializeSeq::end(self)
    }
}

pub struct MapSerializer<'b, 'a, W> {
    serializer: &'b mut Serializer<'a, W>,
    first: bool,
    is_root_map: bool,
}

impl<'b, 'a, W: io::Write> ser::SerializeMap for MapSerializer<'b, 'a, W> {
    type Ok = ();
    type Error = Error;

    fn serialize_key<T>(&mut self, key: &T) -> Result<()>
    where
        T: ?Sized + Serialize,
    {
        if !self.first || !self.is_root_map {
            self.serializer.writer.write_all(b"\n")?;
        }
        self.first = false;

        self.serializer.write_indent()?;
        key.serialize(&mut *self.serializer)?;
        self.serializer.writer.write_all(b":")?;
        Ok(())
    }

    fn serialize_value<T>(&mut self, value: &T) -> Result<()>
    where
        T: ?Sized + Serialize,
    {
        self.serializer.writer.write_all(b" ")?;
        value.serialize(&mut *self.serializer)?;
        Ok(())
    }

    fn end(self) -> Result<()> {
        if !self.is_root_map {
            self.serializer.indent_level -= 1;
        }
        Ok(())
    }
}

impl<'b, 'a, W: io::Write> ser::SerializeStruct for MapSerializer<'b, 'a, W> {
    type Ok = ();
    type Error = Error;
    fn serialize_field<T>(&mut self, key: &'static str, value: &T) -> Result<()>
    where
        T: ?Sized + Serialize,
    {
        ser::SerializeMap::serialize_key(self, key)?;
        ser::SerializeMap::serialize_value(self, value)
    }
    fn end(self) -> Result<()> {
        ser::SerializeMap::end(self)
    }
}
impl<'b, 'a, W: io::Write> ser::SerializeStructVariant for MapSerializer<'b, 'a, W> {
    type Ok = ();
    type Error = Error;
    fn serialize_field<T>(&mut self, key: &'static str, value: &T) -> Result<()>
    where
        T: ?Sized + Serialize,
    {
        ser::SerializeMap::serialize_key(self, key)?;
        ser::SerializeMap::serialize_value(self, value)
    }
    fn end(self) -> Result<()> {
        ser::SerializeMap::end(self)
    }
}

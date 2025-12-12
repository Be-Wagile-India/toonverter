use serde::{ser, Serialize};
use std::io;

pub struct Serializer<W> {
    writer: W,
    indent_level: usize,
    indent_size: usize,
    is_root: bool,
    in_list: bool,
}

impl<W: io::Write> Serializer<W> {
    pub fn new(writer: W) -> Self {
        Serializer {
            writer,
            indent_level: 0,
            indent_size: 2,
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

impl<'a, W: io::Write> ser::Serializer for &'a mut Serializer<W> {
    type Ok = ();
    type Error = Error;

    type SerializeSeq = ListSerializer<'a, W>;
    type SerializeTuple = ListSerializer<'a, W>;
    type SerializeTupleStruct = ListSerializer<'a, W>;
    type SerializeTupleVariant = ListSerializer<'a, W>;
    type SerializeMap = MapSerializer<'a, W>;
    type SerializeStruct = MapSerializer<'a, W>;
    type SerializeStructVariant = MapSerializer<'a, W>;

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
            .any(|c| matches!(c, ':' | ' ' | '\n' | '[' | ']' | '{' | '}' | ',') || v.is_empty());

        if is_reserved || is_number || has_special_chars {
            self.writer.write_all(format!("{:?}", v).as_bytes())?;
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
        self.writer
            .write_all(format!("[{}]:", len_str).as_bytes())?;
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

pub struct ListSerializer<'a, W> {
    serializer: &'a mut Serializer<W>,
}

impl<'a, W: io::Write> ser::SerializeSeq for ListSerializer<'a, W> {
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

impl<'a, W: io::Write> ser::SerializeTuple for ListSerializer<'a, W> {
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
impl<'a, W: io::Write> ser::SerializeTupleStruct for ListSerializer<'a, W> {
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
impl<'a, W: io::Write> ser::SerializeTupleVariant for ListSerializer<'a, W> {
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

pub struct MapSerializer<'a, W> {
    serializer: &'a mut Serializer<W>,
    first: bool,
    is_root_map: bool,
}

impl<'a, W: io::Write> ser::SerializeMap for MapSerializer<'a, W> {
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

impl<'a, W: io::Write> ser::SerializeStruct for MapSerializer<'a, W> {
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
impl<'a, W: io::Write> ser::SerializeStructVariant for MapSerializer<'a, W> {
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

#[cfg(test)]
mod tests {
    use super::*;
    use serde::Serialize;

    fn to_toon<T: Serialize>(value: &T) -> String {
        let mut buffer = Vec::new();
        let mut serializer = Serializer::new(&mut buffer);
        value.serialize(&mut serializer).unwrap();
        String::from_utf8(buffer).unwrap()
    }

    #[test]
    fn test_serialize_primitives() {
        assert_eq!(to_toon(&true), "true");
        assert_eq!(to_toon(&123), "123");
        assert_eq!(to_toon(&12.34), "12.34");
        assert_eq!(to_toon(&"hello"), "hello");
        assert_eq!(to_toon(&"hello world"), "\"hello world\"");
    }

    #[test]
    fn test_serialize_option() {
        let none: Option<i32> = None;
        let some: Option<i32> = Some(123);
        assert_eq!(to_toon(&none), "null");
        assert_eq!(to_toon(&some), "123");
    }

    #[test]
    fn test_serialize_list() {
        let list = vec![1, 2, 3];
        // [3]:
        //   - 1
        //   - 2
        //   - 3
        let expected = "[3]:\n  - 1\n  - 2\n  - 3";
        assert_eq!(to_toon(&list), expected);
    }

    #[test]
    fn test_serialize_struct() {
        #[derive(Serialize)]
        struct MyStruct {
            a: i32,
            b: String,
        }
        let s = MyStruct {
            a: 1,
            b: "foo".to_string(),
        };
        // a: 1
        // b: foo
        let output = to_toon(&s);
        assert!(output.contains("a: 1"));
        assert!(output.contains("b: foo"));
    }

    #[test]
    fn test_serialize_nested() {
        #[derive(Serialize)]
        struct Nested {
            inner: Vec<i32>,
        }
        let n = Nested { inner: vec![1, 2] };

        let output = to_toon(&n);
        // inner: [2]:\n  - 1\n  - 2
        let expected = "inner: [2]:\n  - 1\n  - 2";
        assert_eq!(output, expected);
    }
}

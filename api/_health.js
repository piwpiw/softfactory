module.exports = (req, res) => {
  const body = JSON.stringify({ status: "ok", now: new Date().toISOString() });
  res.statusCode = 200;
  res.setHeader("Content-Type", "application/json; charset=utf-8");
  res.setHeader("Cache-Control", "no-store");
  res.end(body);
};

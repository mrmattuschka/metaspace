if [[ $# -eq 0 ]] ; then
  echo "Builds a Docker image"
  echo "Usage: $0 new_tag"
  exit 1
fi

LITHOPS_VERSION="2.4.1"
WORKDIR=$PWD

# download lithops and create lithops_codeengine archive
curl -L https://github.com/lithops-cloud/lithops/archive/refs/tags/$LITHOPS_VERSION.zip -o "$WORKDIR/lithops.zip"
unzip lithops.zip "lithops-$LITHOPS_VERSION/lithops/*"
mv "lithops-$LITHOPS_VERSION" lithops_codeengine
cp "$WORKDIR/lithops_codeengine/lithops/serverless/backends/code_engine/entry_point.py" "$WORKDIR/lithops_codeengine/lithopsentry.py"
cd "$WORKDIR/lithops_codeengine"
zip -r "$WORKDIR/lithops_codeengine.zip" ./*
cd $WORKDIR

# build a Docker image
cp "$WORKDIR/../../requirements.txt" .
docker build -f "$WORKDIR/Dockerfile" -t "metaspace2020/metaspace-lithops-ce:$1" .

# cleaning up
rm -rf "$WORKDIR/lithops_codeengine"
rm "$WORKDIR/lithops_codeengine.zip" "$WORKDIR/lithops.zip"
rm "$WORKDIR/requirements.txt"
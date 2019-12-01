var socket = io.connect("http://ec2-18-188-117-168.us-east-2.compute.amazonaws.com:8080");

function SocketInstance()
{
    return socket;
}